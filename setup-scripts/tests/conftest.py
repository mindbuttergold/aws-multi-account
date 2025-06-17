from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from mypy_boto3_sts.type_defs import AssumeRoleResponseTypeDef
from pytest_mock import MockerFixture

from setup_terraform_account_roles import TrustPolicyDocument
from tests.test_ous_accounts_registry import (
  ACCOUNTS_PREFIX,
  AWS_REGION,
  MANAGEMENT_ACCOUNT_EMAIL,
  MANAGEMENT_ACCOUNT_ID,
  MANAGEMENT_ACCOUNT_NAME,
  OUS_ACCOUNTS,
  PARENT_OU_ID,
  S3_BACKEND_BUCKET_NAME,
  TERRAFORM_ADMIN_ROLE_NAME,
)
from utils.models import Account, ManagementAccountDetails, TerraformBackendConfig

TEST_ACCOUNT_COUNT = sum(len(accounts) for accounts in OUS_ACCOUNTS.values())
EXPECTED_ADMIN_ROLE_COUNT = TEST_ACCOUNT_COUNT


@pytest.fixture
def test_data() -> dict[str, str]:
  infrastructure_account = next(
    account
    for account in OUS_ACCOUNTS["Infrastructure"]
    if account["name"] == f"{ACCOUNTS_PREFIX}-infrastructure-production"
  )

  return {
    "region": AWS_REGION,
    "account_id": MANAGEMENT_ACCOUNT_ID,
    "management_account_name": MANAGEMENT_ACCOUNT_NAME,
    "management_account_id": MANAGEMENT_ACCOUNT_ID,
    "infrastructure_account_id": infrastructure_account["id"],
    "role_name": TERRAFORM_ADMIN_ROLE_NAME,
    "bucket_name": S3_BACKEND_BUCKET_NAME,
    "email": MANAGEMENT_ACCOUNT_EMAIL,
    "parent_ou_id": PARENT_OU_ID,
  }


@pytest.fixture
def test_aws_credentials() -> AssumeRoleResponseTypeDef:
  return {
    "Credentials": {
      "AccessKeyId": "test-key",
      "SecretAccessKey": "test-secret",
      "SessionToken": "test-token",
      "Expiration": datetime(1988, 1, 13, 0, 0, 0, tzinfo=timezone.utc),
    },
    "AssumedRoleUser": {"AssumedRoleId": "test-role-id", "Arn": "test-arn"},
    "PackedPolicySize": 123,
    "SourceIdentity": "test-identity",
    "ResponseMetadata": {
      "RequestId": "test-request",
      "HTTPStatusCode": 200,
      "HTTPHeaders": {},
      "RetryAttempts": 0,
      "HostId": "test-host",
    },
  }


@pytest.fixture
def test_trust_policy(test_data: dict[str, str]) -> TrustPolicyDocument:
  return {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {"AWS": f"arn:aws:iam::{test_data['management_account_id']}:root"},
        "Action": "sts:AssumeRole",
      }
    ],
  }


@pytest.fixture
def terraform_config(test_data: dict[str, str]) -> TerraformBackendConfig:
  return TerraformBackendConfig(
    aws_region=test_data["region"],
    terraform_admin_role_name=test_data["role_name"],
    s3_backend_bucket_name=test_data["bucket_name"],
    create_terraform_admin_role=True,
    create_s3_backend_bucket=True,
  )


@pytest.fixture
def test_account_factory(
  terraform_config: TerraformBackendConfig,
) -> Callable[[str, str, str], Account]:
  def _create_account(name: str, id: str, organizational_unit: str) -> Account:
    return Account(
      name=name,
      id=id,
      organizational_unit=organizational_unit,
      terraform_backend_config=terraform_config,
    )

  return _create_account


@pytest.fixture
def mock_sts(mocker: MockerFixture) -> MagicMock:
  return mocker.patch("boto3.client", return_value=MagicMock())


@pytest.fixture
def mock_iam(mocker: MockerFixture) -> MagicMock:
  return mocker.patch("boto3.client", return_value=MagicMock())


@pytest.fixture
def mock_s3(mocker: MockerFixture) -> MagicMock:
  return mocker.patch("boto3.client", return_value=MagicMock())


@pytest.fixture
def mock_aws_clients(mock_sts: MagicMock, mock_iam: MagicMock, mock_s3: MagicMock) -> list[MagicMock]:
  return [mock_sts, mock_iam, mock_s3]


@pytest.fixture
def tmp_account_dir(tmp_path: Path) -> Path:
  account_dir = tmp_path / "test-account"
  account_dir.mkdir()
  return account_dir


@pytest.fixture
def management_account(
  terraform_config: TerraformBackendConfig,
) -> ManagementAccountDetails:
  return ManagementAccountDetails(
    id=MANAGEMENT_ACCOUNT_ID,
    name=MANAGEMENT_ACCOUNT_NAME,
    email=MANAGEMENT_ACCOUNT_EMAIL,
    organizational_unit="Management",
    parent_ou_id=PARENT_OU_ID,
    terraform_backend_config=terraform_config,
  )


@pytest.fixture
def test_accounts(test_account_factory: Callable[[str, str, str], Account]) -> list[Account]:
  return [
    test_account_factory(account["name"], account["id"], ou)
    for ou, ou_accounts in OUS_ACCOUNTS.items()
    for account in ou_accounts
  ]


@pytest.fixture
def account_details_content(test_account: Account) -> str:
  return f"""locals {{
  account_name = "{test_account.name}"
  account_id = "{test_account.id}"
  organizational_unit = "{test_account.organizational_unit}"
  aws_region = "{AWS_REGION}"
  terraform_admin_role_name = "{TERRAFORM_ADMIN_ROLE_NAME}"
  s3_backend_bucket_name = "{S3_BACKEND_BUCKET_NAME}"
}}"""


@pytest.fixture
def terragrunt_content() -> str:
  return """include {
  path = find_in_parent_folders("root.hcl")
}"""


@pytest.fixture
def test_account_data(test_account: Account, test_data: dict[str, str]) -> dict[str, str]:
  return {
    "account_name": test_account.name,
    "account_id": test_account.id,
    "organizational_unit": test_account.organizational_unit,
    "aws_region": test_data["region"],
    "terraform_admin_role_name": test_data["role_name"],
    "s3_backend_bucket_name": test_data["bucket_name"],
  }


@pytest.fixture
def test_account(test_account_factory: Callable[[str, str, str], Account]) -> Account:
  account = next(
    account
    for account in OUS_ACCOUNTS["Infrastructure"]
    if account["name"] == f"{ACCOUNTS_PREFIX}-infrastructure-production"
  )
  return test_account_factory(account["name"], account["id"], "Infrastructure")
