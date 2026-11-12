#!/usr/bin/env python3
"""Muxary's public entry point; CCB remains the compatibility/runtime engine."""
from pathlib import Path
import sys

script_root = Path(__file__).resolve().parent
sys.path.insert(0, str(script_root / 'lib'))

from workbench.cli import run_muxary


if __name__ == '__main__':
    raise SystemExit(run_muxary(sys.argv[1:], script_root=script_root))
