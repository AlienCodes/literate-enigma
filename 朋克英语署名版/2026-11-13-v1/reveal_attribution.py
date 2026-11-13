"""Create a separate PDF copy in which the default-hidden attribution is visible."""
import argparse
from pathlib import Path
from provenance import show_copy

if __name__ == '__main__':
    p=argparse.ArgumentParser(description='显示PDF内的朋克英语来源署名，保留原文件。')
    p.add_argument('source',type=Path)
    p.add_argument('output',type=Path)
    args=p.parse_args()
    show_copy(args.source,args.output)
    print(f'已生成署名显示副本：{args.output}')
