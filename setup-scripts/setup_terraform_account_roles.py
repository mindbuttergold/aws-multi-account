import json
import os
import subprocess
from typing import TYPE_CHECKING, TypedDict

import boto3
from botocore.exceptions import ClientError
from mypy_boto3_iam.client import IAMClient
from mypy_boto3_sts.type_defs import CredentialsTypeDef

from utils import config, parse_ous_accounts_data

if TYPE_CHECKING:
  from mypy_boto3_sts.client import STSClient
  from mypy_boto3_sts.type_defs import AssumeRoleResponseTypeDef

  from utils.models import ManagementAccountDetails, TerraformBackendConfig

ROLE_SESSION_NAME = "TerragruntSession"
TERRAFORM_ADMIN_POLICY_NAME = "TerraformAdmin"
ACCOUNT_DETAILS_FILENAME = "account_details.hcl"
TERRAGRUNT_HCL_FILENAME = "terragrunt.hcl"

TERRAFORM_ADMIN_POLICY_DOCUMENT = {
  "Version": "2012-10-17",
  "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}],
}


class RoleAssumptionError(ValueError):
  def __init__(self, account_id: str) -> None:
    super().__init__(f"Error assuming role in account {account_id}")


def get_aws_org_accounts() -> dict[str, str]:
  org_client = boto3.client("organizations")
  accounts: dict[str, str] = {}

  try:
    paginator = org_client.get_paginator("list_accounts")
    for page in paginator.paginate():
      for account in page["Accounts"]:
        accounts[account["Name"]] = account["Id"]
  except ClientError as e:
    error_msg = f"Error retrieving accounts: {e}"
    print(error_msg)
    raise ValueError(error_msg) from e

  if not accounts:
    error_msg = "No accounts found in the organization"
    raise ValueError(error_msg)
  return accounts


def assume_org_account_access_role(account_id: str) -> CredentialsTypeDef:
  sts_client: STSClient = boto3.client("sts")
  role_name: str = "OrganizationAccountAccessRole"
  role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"

  try:
    response: AssumeRoleResponseTypeDef = sts_client.assume_role(RoleArn=role_arn, RoleSessionName=ROLE_SESSION_NAME)
    print(f"Assumed role {role_name} in account {account_id}")
  except ClientError as e:
    raise RoleAssumptionError(account_id) from e
  else:
    return {
      "AccessKeyId": response["Credentials"]["AccessKeyId"],
      "SecretAccessKey": response["Credentials"]["SecretAccessKey"],
      "SessionToken": response["Credentials"]["SessionToken"],
      "Expiration": response["Credentials"]["Expiration"],
    }


def new_iam_client(credentials: CredentialsTypeDef) -> IAMClient:
  client: IAMClient = boto3.client(
    "iam",
    aws_access_key_id=credentials["AccessKeyId"],
    aws_secret_access_key=credentials["SecretAccessKey"],
    aws_session_token=credentials["SessionToken"],
  )
  return client


class TrustPolicyDocument(TypedDict):
  Version: str
  Statement: list[dict]


def terraform_admin_role_trust_policy(
  management_account_id: str,
) -> TrustPolicyDocument:
  return {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {"AWS": f"arn:aws:iam::{management_account_id}:root"},
        "Action": "sts:AssumeRole",
      }
    ],
  }


def create_iam_role(iam_client: IAMClient, role_name: str, trust_policy: TrustPolicyDocument) -> bool:
  try:
    iam_client.create_role(RoleName=role_name, AssumeRolePolicyDocument=json.dumps(trust_policy))
  except ClientError as e:
    if e.response["Error"]["Code"] == "EntityAlreadyExists":
      print(f"Role {role_name} already exists, skipping...")
      return False
    error_msg = f"Error creating IAM role {role_name}: {e}"
    print(error_msg)
    raise ValueError(error_msg) from e
  else:
    print(f"Created IAM role {role_name}")
    return True


def attach_exclusive_inline_policy(iam_client: IAMClient, role_name: str) -> None:
  try:
    iam_client.put_role_policy(
      RoleName=role_name,
      PolicyName=TERRAFORM_ADMIN_POLICY_NAME,
      PolicyDocument=json.dumps(TERRAFORM_ADMIN_POLICY_DOCUMENT),
    )
    print(f"Attached exclusive inline policy to role {role_name}")
  except ClientError as e:
    print(f"Warning: Failed to attach inline policy for role {role_name}: {e}")


def create_terraform_admin_role(account_id: str, management_account_id: str, role_name: str) -> bool:
  credentials = assume_org_account_access_role(account_id)
  iam_client = new_iam_client(credentials)
  trust_policy = terraform_admin_role_trust_policy(management_account_id)
  was_created = create_iam_role(iam_client, role_name, trust_policy)
  if was_created:
    attach_exclusive_inline_policy(iam_client, role_name)
  return was_created


def update_account_ids(accounts: dict[str, str], accounts_dir: str) -> None:
  account_dirs = [d for d in os.listdir(accounts_dir) if os.path.isdir(os.path.join(accounts_dir, d))]

  for dir_name in account_dirs:
    account_details_path = os.path.join(accounts_dir, dir_name, ACCOUNT_DETAILS_FILENAME)
    if not os.path.exists(account_details_path):
      print(f"No account_details.hcl found in {dir_name}, skipping")
      continue

    aws_account_id = accounts.get(dir_name)
    if not aws_account_id:
      print(f"No matching AWS account found for directory: {dir_name}")
      continue

    with open(account_details_path) as file:
      content = file.read()

    updated_content = []
    for line in content.splitlines():
      if "account_id" in line:
        updated_content.append(f'  account_id = "{aws_account_id}"')
      else:
        updated_content.append(line)

    with open(account_details_path, "w") as file:
      file.write("\n".join(updated_content))

    print(f"Updated account ID for {dir_name}")


def create_terraform_admin_roles(
  accounts: dict[str, str],
  management_account_id: str,
  role_name: str,
  accounts_dir: str,
) -> None:
  account_dirs = [d for d in os.listdir(accounts_dir) if os.path.isdir(os.path.join(accounts_dir, d))]

  for dir_name in account_dirs:
    account_details_path = os.path.join(accounts_dir, dir_name, ACCOUNT_DETAILS_FILENAME)
    if not os.path.exists(account_details_path):
      continue

    aws_account_id = accounts.get(dir_name)
    if not aws_account_id:
      print(f"No matching AWS account found for directory: {dir_name}")
      continue

    try:
      create_terraform_admin_role(aws_account_id, management_account_id, role_name)
    except Exception as e:
      print(f"Error creating {role_name} role in {dir_name}: {e}")


def find_terragrunt_directories(base_dir: str) -> list[str]:
  return [
    os.path.join(root, dir_name)
    for root, dirs, _ in os.walk(base_dir)
    for dir_name in dirs
    if os.path.exists(os.path.join(root, dir_name, TERRAGRUNT_HCL_FILENAME))
  ]


def terragrunt_init_account_dirs(base_dir: str) -> None:
  terragrunt_dirs = find_terragrunt_directories(base_dir)

  for dir_path in terragrunt_dirs:
    try:
      subprocess.run(
        ["terragrunt", "hclfmt"],
        cwd=dir_path,
        check=True,
        capture_output=True,
      )
      print(f"Formatted HCL files in {dir_path}")

      subprocess.run(
        ["terragrunt", "init"],
        cwd=dir_path,
        check=True,
      )
      print(f"Initialized Terragrunt in {dir_path}")
    except subprocess.CalledProcessError as e:
      print(f"Error formatting and initializing Terragrunt in {dir_path}: {e}")


def main() -> None:
  aws_org_accounts = get_aws_org_accounts()
  accounts_dir = config.ACCOUNTS_DIRECTORY_PATH

  update_account_ids(aws_org_accounts, accounts_dir)

  management_account_details: ManagementAccountDetails = parse_ous_accounts_data.get_management_account_details()
  terraform_backend_config: TerraformBackendConfig = parse_ous_accounts_data.get_terraform_backend_config()

  create_terraform_admin_roles(
    aws_org_accounts,
    management_account_details.id,
    terraform_backend_config.terraform_admin_role_name,
    accounts_dir,
  )

  terragrunt_init_account_dirs(accounts_dir)


if __name__ == "__main__":
  main()
