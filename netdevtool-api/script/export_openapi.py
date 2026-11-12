"""导出 FastAPI 的 OpenAPI 文档。

用法（在 netdevtool-api 目录下执行）：
    python script/export_openapi.py                  # 输出到项目根目录 openapi.json
    python script/export_openapi.py -o api.json      # 指定文件名
    python script/export_openapi.py --indent 0       # 紧凑输出（不换行）
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.main import app  # noqa: E402  需先加入项目根目录才能导入


def main() -> None:
    parser = argparse.ArgumentParser(description="导出 FastAPI 的 OpenAPI 文档")
    parser.add_argument(
        "-o",
        "--output",
        default="openapi.json",
        help="输出文件路径，相对路径以项目根目录为基准（默认 openapi.json）",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON 缩进空格数，0 表示紧凑输出（默认 2）",
    )
    args = parser.parse_args()

    output = Path(args.output)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)

    spec = app.openapi()
    indent = args.indent if args.indent > 0 else None
    output.write_text(
        json.dumps(spec, ensure_ascii=False, indent=indent),
        encoding="utf-8",
    )

    print(f"已导出 OpenAPI 文档：{output}")
    print(f"接口数量：{len(spec.get('paths', {}))}")


if __name__ == "__main__":
    main()
