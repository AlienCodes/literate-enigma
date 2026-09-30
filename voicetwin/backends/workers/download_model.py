"""下载模型到本地目录（在引擎自己的 Python 环境中运行）。

优先 Hugging Face（可用 HF_ENDPOINT=https://hf-mirror.com 加速），失败时尝试 ModelScope（国内快）。
用法：python download_model.py <repo_id> <local_dir> [auto|hf|modelscope]
"""

import os
import sys


def via_hf(repo: str, local_dir: str) -> None:
    from huggingface_hub import snapshot_download

    snapshot_download(repo_id=repo, local_dir=local_dir)


def via_modelscope(repo: str, local_dir: str) -> None:
    from modelscope import snapshot_download

    snapshot_download(repo, local_dir=local_dir)


def main() -> None:
    repo, local_dir = sys.argv[1], sys.argv[2]
    source = sys.argv[3] if len(sys.argv) > 3 else "auto"
    os.makedirs(local_dir, exist_ok=True)
    order = {"hf": [via_hf], "modelscope": [via_modelscope]}.get(source, [via_hf, via_modelscope])
    errors = []
    for fn in order:
        try:
            print(f"[voicetwin] 下载 {repo} → {local_dir}（{fn.__name__}）", file=sys.stderr)
            fn(repo, local_dir)
            print("[voicetwin] 下载完成", file=sys.stderr)
            return
        except Exception as exc:
            errors.append(f"{fn.__name__}: {exc}")
    print("[voicetwin] 下载失败：\n" + "\n".join(errors), file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
