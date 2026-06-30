"""Command-line entry point for the demo pipeline."""

from __future__ import annotations

import json
import sys

from .pipeline import result_to_dict, run_demo_pipeline


def main() -> int:
    competitor_name = sys.argv[1] if len(sys.argv) > 1 else "HubSpot"
    result = run_demo_pipeline(competitor_name)
    print(json.dumps(result_to_dict(result), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
