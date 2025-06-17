import os
import subprocess
from pathlib import Path

import hcl2
import pytest


class AccountDirError(RuntimeError):
  MISSING_DIR = "accounts directory is missing"
  NO_ACCOUNTS = "no account directories found in accounts/"


def load_hcl_file(file_path: str | Path) -> dict:
  with open(file_path) as f:
    return hcl2.load(f)


def get_account_dirs() -> list[Path]:
  base_path = Path(__file__).parent / "accounts"
  if not base_path.exists() or not base_path.is_dir():
    raise AccountDirError(AccountDirError.MISSING_DIR)

  account_dirs = [d for d in base_path.iterdir() if d.is_dir()]
  if not account_dirs:
    raise AccountDirError(AccountDirError.NO_ACCOUNTS)

  return account_dirs


def test_account_structure_consistency() -> None:
  account_dirs = get_account_dirs()

  required_files = [
    "account_details.hcl",
    "terragrunt.hcl",
    "provider.tf",
    "variables.tf",
  ]

  for account_dir in account_dirs:
    for required_file in required_files:
      file_path = account_dir / required_file
      assert file_path.exists(), f"{required_file} missing in {account_dir}"


def test_backend_configuration() -> None:
  account_dirs = get_account_dirs()

  for account_dir in account_dirs:
    terragrunt_file = account_dir / "terragrunt.hcl"
    config = load_hcl_file(terragrunt_file)

    assert "include" in config, f"Missing include block in {terragrunt_file}"
    include = config["include"][0]
    assert include["path"] == '${find_in_parent_folders("root.hcl")}'


def test_organization_structure() -> None:
  management_dirs = [d for d in get_account_dirs() if "ous_accounts.tf" in os.listdir(d)]
  if not management_dirs:
    pytest.skip("No management account with ous_accounts.tf found")

  ous_file = management_dirs[0] / "ous_accounts.tf"
  config = load_hcl_file(ous_file)

  found_ous = set()
  for resource in config.get("resource", []):
    if "aws_organizations_organizational_unit" in resource:
      for ou_name in resource["aws_organizations_organizational_unit"]:
        found_ous.add(ou_name)

  assert len(found_ous) > 0, "No Organization Units defined in ous_accounts.tf"


def test_account_configuration() -> None:
  account_dirs = get_account_dirs()

  for account_dir in account_dirs:
    account_details = account_dir / "account_details.hcl"
    config = load_hcl_file(account_details)

    account_locals = config.get("locals", [{}])[0]
    assert "account_name" in account_locals, f"Account {account_dir} missing account_name"
    assert "account_id" in account_locals, f"Account {account_dir} missing account_id"
    assert "aws_region" in account_locals, f"Account {account_dir} missing aws_region"


def find_relative_path(target_file: str) -> str:
  return str(Path("..") / target_file)


def test_terragrunt_validate() -> None:
  account_dirs = get_account_dirs()

  for account_dir in account_dirs:
    result = subprocess.run(
      ["terragrunt", "hclfmt", "--check"],
      cwd=account_dir,
      capture_output=True,
      text=True,
      check=False,
    )
    assert result.returncode == 0, f"Terragrunt format check failed in {account_dir}:\\n{result.stderr}"


def test_accounts_directory() -> None:
  base_path = Path(__file__).parent / "accounts"
  if not base_path.exists() or not base_path.is_dir():
    pytest.fail(AccountDirError.MISSING_DIR)

  account_dirs = [d for d in base_path.iterdir() if d.is_dir()]
  if not account_dirs:
    pytest.fail(AccountDirError.NO_ACCOUNTS)
