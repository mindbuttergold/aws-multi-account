import os

from utils import config, file_ops, parse_ous_accounts_data
from utils.models import Account

TERRAGRUNT_HCL = """include {
  path = find_in_parent_folders("root.hcl")
}
"""

ACCOUNT_DETAILS_HCL = """locals {{
  account_name = "{account_name}"
  account_id = "{account_id}"
  organizational_unit = "{organizational_unit}"
  aws_region = "{aws_region}"
  terraform_admin_role_name = "{terraform_admin_role_name}"
  s3_backend_bucket_name = "{s3_backend_bucket_name}"
}}
"""


def create_account_terragrunt_files(account_dir: str, **account_details: str) -> None:
  account_details_filename = "account_details.hcl"
  account_details_path = os.path.join(account_dir, account_details_filename)

  file_ops.write_account_file(
    account_details_path,
    ACCOUNT_DETAILS_HCL.format(**account_details),
    account_details_filename,
    account_details["account_name"],
  )

  terragrunt_filename = "terragrunt.hcl"
  terragrunt_path = os.path.join(account_dir, terragrunt_filename)
  file_ops.write_account_file(
    terragrunt_path,
    TERRAGRUNT_HCL,
    terragrunt_filename,
    account_details["account_name"],
  )


def setup_account_directory(account: Account, accounts_dir: str) -> None:
  accounts_dir = os.path.join(accounts_dir, account.name)
  file_ops.create_directory(accounts_dir)

  if not account.terraform_backend_config:
    error_msg = f"Account {account.name} is missing required terraform_backend_config"
    raise ValueError(error_msg)

  account_details = {
    "account_name": account.name,
    "account_id": account.id,
    "organizational_unit": account.organizational_unit,
    "aws_region": account.terraform_backend_config.aws_region,
    "terraform_admin_role_name": (account.terraform_backend_config.terraform_admin_role_name),
    "s3_backend_bucket_name": account.terraform_backend_config.s3_backend_bucket_name,
  }

  create_account_terragrunt_files(str(accounts_dir), **account_details)


def setup_all_account_directories(accounts_data: list[Account]) -> None:
  file_ops.create_directory(config.ACCOUNTS_DIRECTORY_PATH)

  for account in accounts_data:
    setup_account_directory(account, config.ACCOUNTS_DIRECTORY_PATH)


def main() -> None:
  accounts_data = parse_ous_accounts_data.get_accounts_data()
  setup_all_account_directories(accounts_data)


if __name__ == "__main__":
  main()
