# ignoring redefinition of pytest fixture functions
# ruff: noqa: F811

import json
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

if TYPE_CHECKING:
  from mypy_boto3_sts.type_defs import GetCallerIdentityResponseTypeDef

from setup_terraform_backend import (
  create_ous_accounts_terraform_file,
  create_s3_backend_bucket,
  create_terraform_admin_iam_role,
  create_terraform_locals,
  get_current_logged_in_account,
  get_management_account_dir_path,
  setup_terraform_backend,
  verify_logged_into_management_account,
)

# ignoring unused imports from conftest, injected via fixtures
from tests.conftest import (  # noqa: F401
  management_account,
  terraform_config,
  test_account_factory,
  test_accounts,
  test_data,
)
from utils.models import Account, ManagementAccountDetails, TerraformBackendConfig


def test_get_current_logged_in_account(mocker: MockerFixture, test_data: dict[str, str]) -> None:
  mock_sts = mocker.patch("boto3.client", return_value=MagicMock())
  response: GetCallerIdentityResponseTypeDef = {
    "Account": test_data["account_id"],
    "Arn": f"arn:aws:iam::{test_data['account_id']}:root",
    "UserId": "ABCDEFG",
    "ResponseMetadata": {
      "RequestId": "test-id",
      "HTTPStatusCode": 200,
      "HTTPHeaders": {},
      "RetryAttempts": 0,
    },
  }
  mock_sts.return_value.get_caller_identity.return_value = response
  result = get_current_logged_in_account()

  assert result == test_data["account_id"]
  mock_sts.return_value.get_caller_identity.assert_called_once_with()


@pytest.fixture
def verify_params(test_data: dict[str, str]) -> list[tuple[str, str, bool]]:
  return [
    (test_data["management_account_id"], test_data["management_account_id"], False),
    (test_data["infrastructure_account_id"], test_data["management_account_id"], True),
  ]


def test_verify_management_account_success(
  mocker: MockerFixture,
  test_data: dict[str, str],
) -> None:
  current_account = test_data["management_account_id"]
  mocker.patch(
    "setup_terraform_backend.get_current_logged_in_account",
    return_value=current_account,
  )
  verify_logged_into_management_account(current_account)


def test_verify_management_account_failure(
  mocker: MockerFixture,
  test_data: dict[str, str],
) -> None:
  current_account = test_data["infrastructure_account_id"]
  expected_account = test_data["management_account_id"]
  mocker.patch(
    "setup_terraform_backend.get_current_logged_in_account",
    return_value=current_account,
  )
  with pytest.raises(
    ValueError,
    match=f"You are logged into account: {current_account}",
  ):
    verify_logged_into_management_account(expected_account)


def test_create_terraform_admin_role(mocker: MockerFixture, test_data: dict[str, str]) -> None:
  mock_iam = mocker.patch("boto3.client", return_value=MagicMock())

  create_terraform_admin_iam_role(
    test_data["role_name"],
    test_data["account_id"],
    mock_iam.return_value,
  )

  expected_trust_policy = {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {"AWS": f"arn:aws:iam::{test_data['account_id']}:root"},
        "Action": "sts:AssumeRole",
      }
    ],
  }

  mock_iam.return_value.create_role.assert_called_once_with(
    RoleName=test_data["role_name"],
    AssumeRolePolicyDocument=json.dumps(expected_trust_policy),
  )


def test_create_s3_backend_bucket(mocker: MockerFixture, test_data: dict[str, str]) -> None:
  mock_s3 = mocker.patch("boto3.client", return_value=MagicMock())
  create_s3_backend_bucket(
    test_data["bucket_name"],
    test_data["region"],
    mock_s3.return_value,
  )

  mock_s3.return_value.create_bucket.assert_called_once_with(
    Bucket=test_data["bucket_name"],
    CreateBucketConfiguration={"LocationConstraint": test_data["region"]},
  )

  expected_encryption = {"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}
  mock_s3.return_value.put_bucket_encryption.assert_called_once_with(
    Bucket=test_data["bucket_name"],
    ServerSideEncryptionConfiguration=expected_encryption,
  )


def test_setup_terraform_backend(
  mocker: MockerFixture,
  terraform_config: TerraformBackendConfig,
  test_data: dict[str, str],
) -> None:
  mock_iam = MagicMock(name="iam_client")
  mock_s3 = MagicMock(name="s3_client")
  mock_client = mocker.patch("boto3.client", side_effect={"iam": mock_iam, "s3": mock_s3}.get)

  setup_terraform_backend(terraform_config, test_data["account_id"])

  mock_client.assert_has_calls([mocker.call("iam"), mocker.call("s3")])

  expected_trust_policy = {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {"AWS": f"arn:aws:iam::{test_data['account_id']}:root"},
        "Action": "sts:AssumeRole",
      }
    ],
  }
  mock_iam.create_role.assert_called_once_with(
    RoleName=terraform_config.terraform_admin_role_name,
    AssumeRolePolicyDocument=json.dumps(expected_trust_policy),
  )

  expected_role_policy = {
    "Version": "2012-10-17",
    "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}],
  }
  mock_iam.put_role_policy.assert_called_once_with(
    RoleName=terraform_config.terraform_admin_role_name,
    PolicyName=terraform_config.terraform_admin_role_name,
    PolicyDocument=json.dumps(expected_role_policy),
  )

  mock_s3.create_bucket.assert_called_once_with(
    Bucket=terraform_config.s3_backend_bucket_name,
    CreateBucketConfiguration={"LocationConstraint": terraform_config.aws_region},
  )

  expected_encryption = {"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}
  mock_s3.put_bucket_encryption.assert_called_once_with(
    Bucket=terraform_config.s3_backend_bucket_name,
    ServerSideEncryptionConfiguration=expected_encryption,
  )


@pytest.mark.parametrize("dir_exists", [True, False])
def test_get_management_dir_path(
  tmp_path: Path, management_account: ManagementAccountDetails, dir_exists: bool
) -> None:
  if dir_exists:
    management_dir = tmp_path / management_account.name
    management_dir.mkdir()
    result = get_management_account_dir_path(tmp_path, management_account)
    assert Path(result).name == management_account.name
  else:
    with pytest.raises(ValueError, match=f"Management account directory '{management_account.name}' not found in"):
      get_management_account_dir_path(tmp_path, management_account)


def test_create_terraform_locals(
  tmp_path: Path,
  management_account: ManagementAccountDetails,
  test_accounts: list[Account],
  mocker: MockerFixture,
) -> None:
  management_dir = tmp_path / "test-management"
  management_dir.mkdir()

  mock_write = mocker.patch("utils.file_ops.write_account_file")
  create_terraform_locals(
    str(management_dir),
    management_account,
    "test-management",
    ["Management", "Infrastructure"],
    test_accounts,
  )

  mock_write.assert_called_once_with(
    str(management_dir / "locals.tf"),
    mock_write.call_args[0][1],
    "locals.tf",
    "test-management",
  )

  content = mock_write.call_args[0][1]
  required_fields = [
    "parent_ou_id",
    "management_account_email",
    "organizational_units",
    "accounts",
  ]
  for field in required_fields:
    assert field in content


def test_create_ous_accounts_file(tmp_path: Path, mocker: MockerFixture) -> None:
  management_dir = tmp_path / "test-management"
  management_dir.mkdir()

  mock_write = mocker.patch("utils.file_ops.write_account_file")
  create_ous_accounts_terraform_file(str(management_dir), "test-management")

  mock_write.assert_called_once_with(
    str(management_dir / "ous_accounts.tf"),
    mock_write.call_args[0][1],
    "ous_accounts.tf",
    "test-management",
  )

  content = mock_write.call_args[0][1]
  assert "aws_organizations_organizational_unit" in content
  assert "aws_organizations_account" in content
