"""Entry point: python scripts/run.py <validate|diagram|assess> ..."""

import sys

from archdesign.cli import main

if __name__ == "__main__":
    sys.exit(main())
