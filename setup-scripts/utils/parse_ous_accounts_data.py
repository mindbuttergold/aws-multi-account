import importlib.util
import os
from typing import TypedDict

from utils.models import Account, ManagementAccountDetails, TerraformBackendConfig

OUS_ACCOUNTS_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "..", "ous_accounts_registry.py")


class OUSAccountsRegistryError(ImportError):
  def __init__(self) -> None:
    super().__init__("Could not load OU accounts registry")


class OUSAccountsData(TypedDict):
  name: str
  id: str


class OUSAccountsRegistryData(TypedDict):
  ACCOUNTS_PREFIX: str
  AWS_REGION: str
  CREATE_TERRAFORM_ADMIN_ROLE: bool
  TERRAFORM_ADMIN_ROLE_NAME: str
  CREATE_S3_BACKEND_BUCKET: bool
  S3_BACKEND_BUCKET_NAME: str
  MANAGEMENT_ACCOUNT_NAME: str
  MANAGEMENT_ACCOUNT_ID: str
  MANAGEMENT_ACCOUNT_EMAIL: str
  PARENT_OU_ID: str
  OUS_ACCOUNTS: dict[str, list[OUSAccountsData]]


class AccountsData(TypedDict):
  terraform_backend_config: TerraformBackendConfig
  accounts_data: list[Account]
  management_account_details: ManagementAccountDetails


def load_ous_accounts_data() -> OUSAccountsRegistryData:
  spec = importlib.util.spec_from_file_location(
    "ous_accounts_registry",
    OUS_ACCOUNTS_REGISTRY_PATH,
  )
  if not spec or not spec.loader:
    raise OUSAccountsRegistryError()

  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  return {
    "ACCOUNTS_PREFIX": module.ACCOUNTS_PREFIX,
    "AWS_REGION": module.AWS_REGION,
    "CREATE_TERRAFORM_ADMIN_ROLE": module.CREATE_TERRAFORM_ADMIN_ROLE,
    "TERRAFORM_ADMIN_ROLE_NAME": module.TERRAFORM_ADMIN_ROLE_NAME,
    "CREATE_S3_BACKEND_BUCKET": module.CREATE_S3_BACKEND_BUCKET,
    "S3_BACKEND_BUCKET_NAME": module.S3_BACKEND_BUCKET_NAME,
    "MANAGEMENT_ACCOUNT_NAME": module.MANAGEMENT_ACCOUNT_NAME,
    "MANAGEMENT_ACCOUNT_ID": module.MANAGEMENT_ACCOUNT_ID,
    "MANAGEMENT_ACCOUNT_EMAIL": module.MANAGEMENT_ACCOUNT_EMAIL,
    "PARENT_OU_ID": module.PARENT_OU_ID,
    "OUS_ACCOUNTS": module.OUS_ACCOUNTS,
  }


def ous_accounts_data() -> AccountsData:
  data = load_ous_accounts_data()

  terraform_backend_config = TerraformBackendConfig(
    aws_region=data["AWS_REGION"],
    create_terraform_admin_role=data["CREATE_TERRAFORM_ADMIN_ROLE"],
    terraform_admin_role_name=data["TERRAFORM_ADMIN_ROLE_NAME"],
    create_s3_backend_bucket=data["CREATE_S3_BACKEND_BUCKET"],
    s3_backend_bucket_name=data["S3_BACKEND_BUCKET_NAME"],
  )

  accounts_data = []
  for ou_name, accounts in data["OUS_ACCOUNTS"].items():
    for account in accounts:
      accounts_data.append(
        Account(
          name=account["name"],
          id=account["id"],
          organizational_unit=ou_name,
          terraform_backend_config=terraform_backend_config,
        )
      )

  management_ou_name = next(
    ou_name
    for ou_name, accounts in data["OUS_ACCOUNTS"].items()
    if any(account["id"] == data["MANAGEMENT_ACCOUNT_ID"] for account in accounts)
  )

  management_account_details = ManagementAccountDetails(
    name=data["MANAGEMENT_ACCOUNT_NAME"],
    id=data["MANAGEMENT_ACCOUNT_ID"],
    email=data["MANAGEMENT_ACCOUNT_EMAIL"],
    parent_ou_id=data["PARENT_OU_ID"],
    organizational_unit=management_ou_name,
    terraform_backend_config=terraform_backend_config,
  )

  return {
    "terraform_backend_config": terraform_backend_config,
    "accounts_data": accounts_data,
    "management_account_details": management_account_details,
  }


def get_accounts_data() -> list[Account]:
  data = ous_accounts_data()
  return data["accounts_data"]


def get_terraform_backend_config() -> TerraformBackendConfig:
  data = ous_accounts_data()
  return data["terraform_backend_config"]


def get_management_account_details() -> ManagementAccountDetails:
  data = ous_accounts_data()
  return data["management_account_details"]
