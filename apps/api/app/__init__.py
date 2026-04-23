"""Trust Ledger API application package."""

from pathlib import Path
import sys


DOMAIN_ROOT = Path(__file__).resolve().parents[3] / "packages" / "domain"
DOMAIN_ROOT_STR = str(DOMAIN_ROOT)

if DOMAIN_ROOT.exists() and DOMAIN_ROOT_STR not in sys.path:
    sys.path.insert(0, DOMAIN_ROOT_STR)
