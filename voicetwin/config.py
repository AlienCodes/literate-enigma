"""配置加载：内置默认值 + 用户 config.yaml 深度合并。"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

DEFAULT_CONFIG_PATH = Path(__file__).with_name("default_config.yaml")


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


def load_config(path: Optional[str] = None, overrides: Optional[Dict[str, Any]] = None,
                user_config: bool = True) -> Config:
    cfg = load_default()
    user_path = find_user_config(path) if user_config else None
    if user_path is not None:
        with open(user_path, "r", encoding="utf-8") as f:
            cfg = deep_merge(cfg, yaml.safe_load(f) or {})
        base_dir = user_path.parent.resolve()
    else:
        base_dir = Path.cwd().resolve()
    if overrides:
        cfg = deep_merge(cfg, overrides)
    config = Config(cfg)
    config["_base_dir"] = str(base_dir)
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
    text = path.read_text(encoding="utf-8")
    new_text = _apply_replacements(text, replacements)
    if new_text != text:
        _backup(path)
        path.write_text(new_text, encoding="utf-8")
    return path
