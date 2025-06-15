from pathlib import Path

BASE_PATH = Path(__file__).resolve().parent
REPO_ROOT = BASE_PATH.parent.parent
OUS_ACCOUNTS_REGISTRY_PATH = BASE_PATH.parent / "ous_accounts_registry.py"
ACCOUNTS_DIRECTORY_PATH = str(REPO_ROOT / "accounts")


class Colors:
  RED = "\033[91m"
  GREEN = "\033[92m"
  YELLOW = "\033[93m"
  RESET = "\033[0m"
