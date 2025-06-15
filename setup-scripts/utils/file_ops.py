import os

from utils.config import BASE_PATH, Colors


def create_directory(path: str) -> str:
  if not os.path.exists(path):
    os.makedirs(path)
    repo_root = BASE_PATH.parent
    dir_name = os.path.relpath(path, repo_root)
    print(f"\n{Colors.GREEN}Created directory: {dir_name}{Colors.RESET}")
  return path


def write_account_file(path: str, content: str, filename: str, account_name: str) -> None:
  with open(path, "w") as file:
    file.write(content)
    print(f"{Colors.GREEN}Created {filename} in {account_name} directory{Colors.RESET}")
