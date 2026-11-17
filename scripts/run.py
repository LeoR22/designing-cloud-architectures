"""Entry point: python scripts/run.py <extract|validate|diagram|assess> ...

Works under `python -I` (isolated mode), which is how untrusted input files should be read.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from archdesign.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
