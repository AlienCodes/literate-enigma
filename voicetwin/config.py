"""配置加载：内置默认值 + 用户 config.yaml 深度合并。"""

from __future__ import annotations

import copy
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import yaml

DEFAULT_CONFIG_PATH = Path(__file__).with_name("default_config.yaml")
#: v0.1.0～v0.1.3 的默认配置（提交 27a539a / 5b46851）原样写进每个人 config.yaml 的那一行（安装程序会保留旧的 config.yaml）：
#:   quality: balanced           # fast（每句 1 个候选）| balanced（3 个）| best（5 个并用识别校验）
#: 这是当时自动写的默认值，不是老师自己选的，当作 auto（= 默认的「一模一样」）。自己改过的（后面的说明不一样）照常按写的来。
LEGACY_QUALITY_RE = re.compile(r"^[ \t]+quality:[ \t]*balanced[ \t]+#[ \t]*fast（每句 1 个候选）", re.M)


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


class Config(dict):
    """dict 子类，支持 cfg.get_path("a.b.c") 这样的点号访问。"""

    def get_path(self, dotted: str, default: Any = None) -> Any:
        node: Any = self
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def set_path(self, dotted: str, value: Any) -> None:
        parts = dotted.split(".")
        node: Dict[str, Any] = self
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value

    def backend(self, name: str) -> Dict[str, Any]:
        return dict(self.get("backends", {}).get(name, {}) or {})


def load_default() -> Dict[str, Any]:
    with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def find_user_config(explicit: Optional[str] = None) -> Optional[Path]:
    if explicit:
        p = Path(explicit)
        if not p.exists():
            raise FileNotFoundError(f"找不到配置文件：{p}")
        return p
    env = os.environ.get("VOICETWIN_CONFIG")
    if env and Path(env).exists():
        return Path(env)
    for candidate in (Path.cwd() / "config.yaml", Path.cwd() / "voicetwin.yaml"):
        if candidate.exists():
            return candidate
    return None


class ConfigError(ValueError):
    """config.yaml 读不了或格式不对。消息是给老师看的中文，包含解决办法。"""


FIX_HINT = ("解决办法：如果同一个文件夹里有 config.yaml.bak（上一次的备份），把它改名为 config.yaml 覆盖它；"
            "没有的话，删掉 config.yaml，再双击 install_windows.bat 重新生成。")


def read_text_any(path: Path) -> Tuple[str, str]:
    """读取文本文件，返回（内容, 编码）。先按 UTF-8（带不带 BOM 都行），不行再按 GBK（记事本「ANSI」）。"""
    data = Path(path).read_bytes()
    try:
        text, encoding = data.decode("utf-8-sig"), "utf-8"
    except UnicodeDecodeError:
        try:
            text, encoding = data.decode("gbk"), "gbk"
        except UnicodeDecodeError as exc:
            raise ConfigError(f"设置文件 {path} 的编码看不懂（既不是 UTF-8 也不是 GBK）。{FIX_HINT}") from exc
    # 和 read_text() 一样统一换行符，写回时才不会变成 \r\r\n
    return text.replace("\r\n", "\n").replace("\r", "\n"), encoding


def parse_user_yaml(text: str, path: Path) -> Dict[str, Any]:
    """解析用户的 config.yaml；格式不对时抛出带行号和解决办法的中文 ConfigError。"""
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None) or getattr(exc, "context_mark", None)
        where = f"第 {mark.line + 1} 行" if mark is not None and getattr(mark, "line", None) is not None else ""
        raise ConfigError(f"设置文件 {path} {where}格式不对（常见原因：前面的空格数不对，或者冒号后面少了一个空格）。"
                          f"{FIX_HINT}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(f"设置文件 {path} 的内容不对（应该是一行一行「名字: 值」这样的设置）。{FIX_HINT}")
    return data


def load_config(path: Optional[str] = None, overrides: Optional[Dict[str, Any]] = None,
                user_config: bool = True) -> Config:
    cfg = load_default()
    user_path = find_user_config(path) if user_config else None
    if user_path is not None:
        text, encoding = read_text_any(user_path)
        if encoding != "utf-8":
            from voicetwin.utils.log import get_logger

            get_logger("config").warning(f"{user_path.name} 不是 UTF-8 编码，已按 GBK 读取")
        user = parse_user_yaml(text, user_path)
        cfg = deep_merge(cfg, user)
        base_dir = user_path.parent.resolve()
        synth = user.get("synth")
        legacy = bool(LEGACY_QUALITY_RE.search(text)) and isinstance(synth, dict) and synth.get("quality") == "balanced"
    else:
        base_dir = Path.cwd().resolve()
        legacy = False
    if legacy and isinstance(cfg.get("synth"), dict):
        cfg["synth"]["quality"] = "auto"
    if overrides:
        cfg = deep_merge(cfg, overrides)
    config = Config(cfg)
    config["_base_dir"] = str(base_dir)
    if legacy and config.get_path("synth.quality") == "auto":
        config["_legacy_quality"] = "balanced"  # 命令行据此说明一句（见 cli._config_quality_notes）
    return config


def resolve_path(cfg: Config, value: Optional[str]) -> Optional[Path]:
    """把配置里的相对路径解析为相对于 config.yaml 所在目录的绝对路径。"""
    if value in (None, ""):
        return None
    p = Path(os.path.expanduser(str(value)))
    if not p.is_absolute():
        p = Path(cfg.get("_base_dir", ".")) / p
    return p.resolve()


def _apply_replacements(text: str, replacements: Optional[Dict[str, str]]) -> str:
    """在保留注释和格式的前提下，替换 YAML 文本里指定键的值。键形如 "backends.gptsovits.root"。"""
    import re

    for dotted, value in (replacements or {}).items():
        parts = dotted.split(".")
        pos, indent = 0, 0
        for depth, key in enumerate(parts):
            m = re.compile(rf"^{' ' * indent}{re.escape(key)}:(.*)$", re.M).search(text, pos)
            if not m:
                raise KeyError(dotted)
            if depth == len(parts) - 1:
                rest = m.group(1)
                comment = rest[rest.index("#"):] if "#" in rest else ""
                quoted = json.dumps(str(value), ensure_ascii=False)
                line = f"{' ' * indent}{key}: {quoted}" + (f"  {comment}" if comment else "")
                text = text[:m.start()] + line + text[m.end():]
            else:
                pos, indent = m.end(), indent + 2
    return text


def _backup(path: Path) -> None:
    import shutil

    shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))


def write_example_config(dest: Path, replacements: Optional[Dict[str, str]] = None, overwrite: bool = False) -> Path:
    """生成带中文注释的 config.yaml。replacements 形如 {"backends.gptsovits.root": "D:/GPT-SoVITS"}。"""
    dest = Path(dest)
    if dest.exists() and not overwrite:
        raise FileExistsError(f"{dest} 已存在，未覆盖。")
    if dest.exists():
        _backup(dest)  # 覆盖前备份
    text = _apply_replacements(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"), replacements)
    dest.write_text(text, encoding="utf-8")
    return dest


def update_config_file(path: Path, replacements: Dict[str, str]) -> Path:
    """只修改已有 config.yaml 里的指定项，其余设置和注释原样保留。"""
    path = Path(path)
    text, _ = read_text_any(path)  # 记事本另存为 ANSI（GBK）的也能改；写回时统一存成 UTF-8
    new_text = _apply_replacements(text, replacements)
    if new_text != text:
        _backup(path)
        path.write_text(new_text, encoding="utf-8")
    return path
