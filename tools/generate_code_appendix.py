from __future__ import annotations

import argparse
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_code_resources import load_code_resources, render_appendix  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic textbook Appendix D")
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rendered = render_appendix(load_code_resources(args.mapping))
    if args.check:
        if not args.output.is_file() or args.output.read_text(encoding="utf-8") != rendered:
            print(f"Appendix D is not synchronized with {args.mapping}", file=sys.stderr)
            return 1
        print("Appendix D is synchronized")
        return 0
    args.output.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
