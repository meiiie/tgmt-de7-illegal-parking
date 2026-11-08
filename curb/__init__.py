"""Local video operations for parking review."""

import json
from pathlib import Path

PRODUCT = json.loads(Path(__file__).with_name("product.json").read_text(encoding="utf-8"))
__version__ = PRODUCT["version"]
