import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, cast

import boto3
from mypy_boto3_iam.client import IAMClient
from mypy_boto3_s3.client import S3Client
from mypy_boto3_s3.type_defs import (
  ServerSideEncryptionByDefaultTypeDef,
  ServerSideEncryptionConfigurationTypeDef,
  ServerSideEncryptionRuleTypeDef,
)

if TYPE_CHECKING:
  from mypy_boto3_s3.literals import BucketLocationConstraintType

from utils import file_ops, parse_ous_accounts_data
from utils.config import ACCOUNTS_DIRECTORY_PATH, Colors
from utils.models import Account, ManagementAccountDetails, TerraformBackendConfig

if TYPE_CHECKING:
  from mypy_boto3_sts.client import STSClient
  from mypy_boto3_sts.type_defs import GetCallerIdentityResponseTypeDef

OUS_TERRAFORM_RESOURCE = """resource "aws_organizations_organizational_unit" "managed" {
  for_each  = toset(local.organizational_units)
  name      = each.value
  parent_id = local.parent_ou_id
}
"""

ACCOUNTS_TERRAFORM_RESOURCE = """resource "aws_organizations_account" "managed" {
  for_each = {
    for account in local.accounts :
    account.name => account
    if account.organizational_unit != "Management"
  }
  name      = each.value.name
  email     = replace(local.management_account_email, "@", "+${each.value.name}@")
  parent_id = aws_organizations_organizational_unit.managed[each.value.organizational_unit].id
}
"""


def get_current_logged_in_account() -> str:
  sts_client: STSClient = boto3.client("sts")
  response: GetCallerIdentityResponseTypeDef = sts_client.get_caller_identity()
  return response["Account"]


def verify_logged_into_management_account(management_account_id: str) -> None:
  current_logged_in_id = get_current_logged_in_account()
  if current_logged_in_id != management_account_id:
    error_msg = (
      f"You are logged into account: {current_logged_in_id}. "
      f"Must be logged into your management account. You have that in "
      f"ous_accounts_registry.py as account: {management_account_id}"
    )
    raise ValueError(error_msg)


def create_terraform_admin_iam_role(
  terraform_admin_role_name: str, management_account_id: str, iam_client: IAMClient
) -> None:
  trust_policy = {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {"AWS": f"arn:aws:iam::{management_account_id}:root"},
        "Action": "sts:AssumeRole",
      }
    ],
  }

  iam_client.create_role(
    RoleName=terraform_admin_role_name,
    AssumeRolePolicyDocument=json.dumps(trust_policy),
  )
  print(f"{Colors.GREEN}Created IAM role: {terraform_admin_role_name}{Colors.RESET}")


def attach_terraform_admin_role_policy(terraform_admin_role_name: str, iam_client: IAMClient) -> None:
  role_policy = {
    "Version": "2012-10-17",
    "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}],
  }

  iam_client.put_role_policy(
    RoleName=terraform_admin_role_name,
    PolicyName=terraform_admin_role_name,
    PolicyDocument=json.dumps(role_policy),
  )
  print(f"{Colors.GREEN}Attached {terraform_admin_role_name} policy to role: {terraform_admin_role_name}{Colors.RESET}")


def create_s3_backend_bucket(s3_backend_bucket_name: str, aws_region: str, s3_client: S3Client) -> None:
  s3_client.create_bucket(
    Bucket=s3_backend_bucket_name,
    CreateBucketConfiguration={"LocationConstraint": cast("BucketLocationConstraintType", aws_region)},
  )
  print(f"{Colors.GREEN}Created S3 bucket: {s3_backend_bucket_name}{Colors.RESET}")

  server_side_encryption = ServerSideEncryptionByDefaultTypeDef(SSEAlgorithm="AES256")
  encryption_rule = ServerSideEncryptionRuleTypeDef(ApplyServerSideEncryptionByDefault=server_side_encryption)
  encryption_config = ServerSideEncryptionConfigurationTypeDef(Rules=[encryption_rule])
  s3_client.put_bucket_encryption(
    Bucket=s3_backend_bucket_name,
    ServerSideEncryptionConfiguration=encryption_config,
  )
  print(f"{Colors.GREEN}Enabled encryption for bucket: {s3_backend_bucket_name}{Colors.RESET}")

  s3_client.put_bucket_versioning(Bucket=s3_backend_bucket_name, VersioningConfiguration={"Status": "Enabled"})
  print(f"{Colors.GREEN}Created encrypted S3 bucket for terraform backend: {s3_backend_bucket_name}{Colors.RESET}")


def setup_terraform_backend(terraform_backend_config: TerraformBackendConfig, management_account_id: str) -> None:
  if terraform_backend_config.create_terraform_admin_role:
    iam_client = boto3.client("iam")
    create_terraform_admin_iam_role(
      terraform_backend_config.terraform_admin_role_name,
      management_account_id,
      iam_client,
    )
    attach_terraform_admin_role_policy(terraform_backend_config.terraform_admin_role_name, iam_client)

  if terraform_backend_config.create_s3_backend_bucket:
    s3_client = boto3.client("s3")
    create_s3_backend_bucket(
      terraform_backend_config.s3_backend_bucket_name,
      terraform_backend_config.aws_region,
      s3_client,
    )


def get_management_account_dir_path(accounts_dir: str | Path, management_account: ManagementAccountDetails) -> str:
  management_dir = os.path.join(accounts_dir, management_account.name)
  if not os.path.exists(management_dir):
    error_msg = f"Management account directory '{management_account.name}' not found in: {accounts_dir}"
    raise ValueError(error_msg)
  return management_dir


def create_terraform_locals(
  management_account_dir_path: str,
  management_account_details: ManagementAccountDetails,
  management_account_name: str,
  ou_names_list: list[str],
  accounts_data: list[Account],
) -> None:
  filename = "locals.tf"
  locals_path = os.path.join(management_account_dir_path, filename)

  account_objects = []
  for account in accounts_data:
    account_objects.append({"name": account.name, "organizational_unit": account.organizational_unit})

  content = f"""locals {{
  parent_ou_id = "{management_account_details.parent_ou_id}"
  management_account_email = "{management_account_details.email}"
  organizational_units = {json.dumps(ou_names_list)}
  accounts = {json.dumps(account_objects, indent=2)}
}}
"""
  file_ops.write_account_file(locals_path, content, filename, management_account_name)


def create_ous_accounts_terraform_file(management_account_dir_path: str, management_account_name: str) -> None:
  content = f"{OUS_TERRAFORM_RESOURCE}\n{ACCOUNTS_TERRAFORM_RESOURCE}"
  filename = "ous_accounts.tf"
  ous_accounts_path = os.path.join(management_account_dir_path, filename)
  file_ops.write_account_file(ous_accounts_path, content, filename, management_account_name)


def setup_terraform_resource_files(
  accounts_dir_path: str,
  management_account_details: ManagementAccountDetails,
  accounts_data: list[Account],
) -> None:
  management_account_dir_path = get_management_account_dir_path(accounts_dir_path, management_account_details)
  management_account_name = management_account_details.name

  ou_names_list = list({account.organizational_unit for account in accounts_data})
  ou_names_list.sort()

  create_terraform_locals(
    management_account_dir_path,
    management_account_details,
    management_account_name,
    ou_names_list,
    accounts_data,
  )

  create_ous_accounts_terraform_file(management_account_dir_path, management_account_name)


def main() -> None:
  management_account_details = parse_ous_accounts_data.get_management_account_details()
  management_account_id = management_account_details.id

  verify_logged_into_management_account(management_account_id)

  terraform_backend_config = parse_ous_accounts_data.get_terraform_backend_config()
  setup_terraform_backend(terraform_backend_config, management_account_id)

  accounts_data = parse_ous_accounts_data.get_accounts_data()
  setup_terraform_resource_files(ACCOUNTS_DIRECTORY_PATH, management_account_details, accounts_data)


if __name__ == "__main__":
  main()
