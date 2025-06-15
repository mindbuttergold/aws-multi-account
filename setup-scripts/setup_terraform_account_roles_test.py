# ignoring redefinition of pytest fixture functions
# ruff: noqa: F811

import json
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError
from mypy_boto3_iam.client import IAMClient
from mypy_boto3_organizations.client import OrganizationsClient
from mypy_boto3_sts.client import STSClient
from mypy_boto3_sts.type_defs import AssumeRoleResponseTypeDef
from pytest_mock import MockerFixture

if TYPE_CHECKING:
  from mypy_boto3_organizations.type_defs import AccountTypeDef

from setup_terraform_account_roles import (
  RoleAssumptionError,
  TrustPolicyDocument,
  assume_org_account_access_role,
  attach_exclusive_inline_policy,
  create_iam_role,
  create_terraform_admin_role,
  create_terraform_admin_roles,
  find_terragrunt_directories,
  get_aws_org_accounts,
  main,
  terragrunt_init_account_dirs,
  update_account_ids,
)

# ignoring unused imports from conftest, injected via fixtures
from tests.conftest import (  # noqa: F401
  EXPECTED_ADMIN_ROLE_COUNT,
  terraform_config,
  test_account,
  test_account_data,
  test_account_factory,
  test_accounts,
  test_aws_credentials,
  test_data,
  test_trust_policy,
)
from utils.models import Account

EXPECTED_TERRAGRUNT_CALLS = 2


@pytest.fixture
def mock_boto3(mocker: MockerFixture) -> Generator[MagicMock, None, None]:
  mock_client = mocker.patch("boto3.client")
  mock_clients: dict[str, MagicMock] = {}

  def get_client(
    service_name: str,
    *,
    aws_access_key_id: str = "",
    aws_secret_access_key: str = "",
    aws_session_token: str = "",
  ) -> MagicMock:
    if service_name not in mock_clients:
      mock = MagicMock()
      if service_name == "sts":
        mock.spec = STSClient
      elif service_name == "iam":
        mock.spec = IAMClient
      elif service_name == "organizations":
        mock.spec = OrganizationsClient

      service_configs = {
        "sts": {"assume_role": MagicMock()},
        "iam": {"create_role": MagicMock(), "put_role_policy": MagicMock()},
        "organizations": {"get_paginator": MagicMock()},
      }
      for attr, value in service_configs.get(service_name, {}).items():
        setattr(mock, attr, value)
      mock_clients[service_name] = mock
    return mock_clients[service_name]

  mock_client.side_effect = get_client
  return mock_client


@pytest.fixture
def mock_sts_client(mock_boto3: MagicMock) -> MagicMock:
  client: MagicMock = mock_boto3("sts")
  client.spec = STSClient
  return client


@pytest.fixture
def mock_iam_client(mock_boto3: MagicMock) -> MagicMock:
  client: MagicMock = mock_boto3("iam")
  client.spec = IAMClient
  return client


@pytest.mark.parametrize(
  ("error_code", "error_message"),
  [
    ("AccessDenied", "Access Denied"),
    ("ValidationError", "Invalid input"),
  ],
)
def test_assume_org_account_access_role_failure(
  mock_sts_client: MagicMock,
  error_code: str,
  error_message: str,
  test_data: dict[str, str],
) -> None:
  mock_sts_client.assume_role.side_effect = ClientError(
    {"Error": {"Code": error_code, "Message": error_message}},
    "AssumeRole",
  )

  with pytest.raises(RoleAssumptionError):
    assume_org_account_access_role(test_data["account_id"])


def test_assume_org_account_access_role_success(
  mock_sts_client: MagicMock,
  test_data: dict[str, str],
  test_aws_credentials: AssumeRoleResponseTypeDef,
) -> None:
  mock_sts_client.assume_role.return_value = test_aws_credentials
  result = assume_org_account_access_role(test_data["account_id"])

  assert isinstance(result, dict)
  assert result["AccessKeyId"] == "test-key"
  assert result["SecretAccessKey"] == "test-secret"
  assert result["SessionToken"] == "test-token"
  assert result["Expiration"] is not None

  expected_role_arn = f"arn:aws:iam::{test_data['account_id']}:role/OrganizationAccountAccessRole"
  expected_session = "TerragruntSession"

  mock_sts_client.assume_role.assert_called_once_with(RoleArn=expected_role_arn, RoleSessionName=expected_session)


def test_create_iam_role_success(
  mock_iam_client: MagicMock,
  test_data: dict[str, str],
  test_trust_policy: TrustPolicyDocument,
) -> None:
  result = create_iam_role(mock_iam_client, test_data["role_name"], test_trust_policy)

  assert result is True
  mock_iam_client.create_role.assert_called_once_with(
    RoleName=test_data["role_name"],
    AssumeRolePolicyDocument=json.dumps(test_trust_policy),
  )


def test_create_iam_role_already_exists(
  mock_iam_client: MagicMock,
  test_data: dict[str, str],
  test_trust_policy: TrustPolicyDocument,
) -> None:
  mock_iam_client.create_role.side_effect = ClientError(
    {"Error": {"Code": "EntityAlreadyExists", "Message": "Role exists"}},
    "CreateRole",
  )

  result = create_iam_role(mock_iam_client, test_data["role_name"], test_trust_policy)

  assert result is False
  mock_iam_client.create_role.assert_called_once_with(
    RoleName=test_data["role_name"],
    AssumeRolePolicyDocument=json.dumps(test_trust_policy),
  )


def test_get_aws_org_accounts_success(
  mock_boto3: MagicMock,
  test_data: dict[str, str],
) -> None:
  mock_org = mock_boto3("organizations")
  mock_paginator = MagicMock()
  mock_org.get_paginator.return_value = mock_paginator

  accounts: list[AccountTypeDef] = [
    {"Name": "test-account-1", "Id": test_data["account_id"]},
    {"Name": "test-account-2", "Id": test_data["management_account_id"]},
  ]
  mock_paginator.paginate.return_value = [{"Accounts": accounts}]

  result = get_aws_org_accounts()

  expected = {
    "test-account-1": test_data["account_id"],
    "test-account-2": test_data["management_account_id"],
  }
  assert result == expected


def test_get_aws_org_accounts_no_accounts(mock_boto3: MagicMock) -> None:
  mock_org = mock_boto3("organizations")
  mock_paginator = MagicMock()
  mock_org.get_paginator.return_value = mock_paginator
  mock_paginator.paginate.return_value = [{"Accounts": []}]

  with pytest.raises(ValueError, match="No accounts found in the organization"):
    get_aws_org_accounts()


def test_create_terraform_admin_role_success(
  mock_boto3: MagicMock,
  test_data: dict[str, str],
  test_aws_credentials: dict,
  test_trust_policy: dict,
) -> None:
  mock_sts = mock_boto3("sts")
  mock_iam = mock_boto3("iam")
  mock_sts.assume_role.return_value = test_aws_credentials
  mock_iam.create_role.return_value = {
    "Role": {"Arn": f"arn:aws:iam::{test_data['account_id']}:role/{test_data['role_name']}"}
  }

  result = create_terraform_admin_role(
    test_data["account_id"],
    test_data["management_account_id"],
    test_data["role_name"],
  )

  assert result is True
  mock_sts.assume_role.assert_called_once_with(
    RoleArn=f"arn:aws:iam::{test_data['account_id']}:role/OrganizationAccountAccessRole",
    RoleSessionName="TerragruntSession",
  )
  mock_iam.create_role.assert_called_once_with(
    RoleName=test_data["role_name"],
    AssumeRolePolicyDocument=json.dumps(test_trust_policy),
  )
  mock_iam.put_role_policy.assert_called_once_with(
    RoleName=test_data["role_name"],
    PolicyName="TerraformAdmin",
    PolicyDocument=json.dumps(
      {
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}],
      }
    ),
  )


def test_find_terragrunt_directories(tmp_path: Path) -> None:
  test_dir = tmp_path / "test_accounts"
  test_dir.mkdir()
  for i in range(EXPECTED_TERRAGRUNT_CALLS):
    account_dir = test_dir / f"account-{i}"
    account_dir.mkdir()
    (account_dir / "terragrunt.hcl").touch()

  dirs = list(find_terragrunt_directories(str(test_dir)))
  assert len(dirs) == EXPECTED_TERRAGRUNT_CALLS


@pytest.fixture
def mock_get_accounts(mocker: MockerFixture, test_data: dict[str, str]) -> MagicMock:
  mock = mocker.patch("setup_terraform_account_roles.get_aws_org_accounts")
  mock.return_value = {
    "test-account": test_data["account_id"],
    "test-account-2": test_data["management_account_id"],
  }
  return mock


def test_terragrunt_init_account_dirs(tmp_path: Path, mocker: MockerFixture) -> None:
  account_dir = tmp_path / "test-account"
  account_dir.mkdir()
  (account_dir / "terragrunt.hcl").touch()

  mock_run = mocker.patch("subprocess.run")
  terragrunt_init_account_dirs(str(tmp_path))

  assert mock_run.call_count == EXPECTED_TERRAGRUNT_CALLS
  mock_run.assert_has_calls(
    [
      mocker.call(
        ["terragrunt", "hclfmt"],
        cwd=str(account_dir),
        check=True,
        capture_output=True,
      ),
      mocker.call(
        ["terragrunt", "init"],
        cwd=str(account_dir),
        check=True,
      ),
    ]
  )


def test_update_account_ids(tmp_path: Path, test_data: dict[str, str]) -> None:
  account1 = tmp_path / "test-account"
  account1.mkdir()
  account2 = tmp_path / "test-account-2"
  account2.mkdir()

  details1 = account1 / "account_details.hcl"
  details2 = account2 / "account_details.hcl"

  original_content = """locals {
  account_id = "000000000000"
  other_field = "value"
}"""

  details1.write_text(original_content)
  details2.write_text(original_content)

  accounts = {
    "test-account": test_data["account_id"],
    "test-account-2": test_data["management_account_id"],
  }

  update_account_ids(accounts, str(tmp_path))

  content1 = details1.read_text()
  assert f'  account_id = "{test_data["account_id"]}"' in content1
  assert "other_field" in content1

  content2 = details2.read_text()
  assert f'  account_id = "{test_data["management_account_id"]}"' in content2
  assert "other_field" in content2


def test_create_terraform_admin_roles(
  tmp_path: Path,
  mocker: MockerFixture,
  test_data: dict[str, str],
  test_accounts: list[Account],
) -> None:
  accounts = {account.name: account.id for account in test_accounts}
  management_account_id = test_data["management_account_id"]
  role_name = test_data["role_name"]

  for account_name in accounts:
    account_dir = tmp_path / account_name
    account_dir.mkdir()
    (account_dir / "account_details.hcl").touch()

  mock_create_role = mocker.patch(
    "setup_terraform_account_roles.create_terraform_admin_role",
    return_value=True,
  )

  create_terraform_admin_roles(accounts, management_account_id, role_name, str(tmp_path))
  assert mock_create_role.call_count == EXPECTED_ADMIN_ROLE_COUNT


def test_create_terraform_admin_roles_error(tmp_path: Path, mocker: MockerFixture, test_data: dict[str, str]) -> None:
  accounts = {"test-account": test_data["account_id"]}
  management_account_id = test_data["management_account_id"]
  role_name = test_data["role_name"]

  account_dir = tmp_path / "test-account"
  account_dir.mkdir()
  (account_dir / "account_details.hcl").touch()

  mock_create_role = mocker.patch(
    "setup_terraform_account_roles.create_terraform_admin_role",
    side_effect=ValueError("Test error"),
  )

  create_terraform_admin_roles(accounts, management_account_id, role_name, str(tmp_path))
  mock_create_role.assert_called_once_with(test_data["account_id"], management_account_id, role_name)


def test_update_account_ids_no_matching_account(tmp_path: Path, test_data: dict[str, str]) -> None:
  accounts = {"other-account": test_data["account_id"]}

  account_dir = tmp_path / "test-account"
  account_dir.mkdir()
  details_file = account_dir / "account_details.hcl"

  original_content = """locals {
  account_id = "000000000000"
  other_field = "value"
}"""

  details_file.write_text(original_content)

  update_account_ids(accounts, str(tmp_path))

  assert details_file.read_text() == original_content


def test_update_account_ids_no_details_file(tmp_path: Path, test_data: dict[str, str]) -> None:
  accounts = {"test-account": test_data["account_id"]}

  account_dir = tmp_path / "test-account"
  account_dir.mkdir()

  update_account_ids(accounts, str(tmp_path))


def test_attach_exclusive_inline_policy_error(mocker: MockerFixture) -> None:
  mock_iam = MagicMock()
  mock_iam.put_role_policy.side_effect = ClientError(
    {
      "Error": {"Code": "ServiceFailure", "Message": "Internal error"},
      "ResponseMetadata": {
        "RequestId": "test-request",
        "HTTPStatusCode": 500,
        "HTTPHeaders": {},
        "RetryAttempts": 0,
        "HostId": "test-host",
      },
    },
    "PutRolePolicy",
  )

  attach_exclusive_inline_policy(mock_iam, "test-role")

  expected_policy = {
    "Version": "2012-10-17",
    "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}],
  }
  mock_iam.put_role_policy.assert_called_once_with(
    RoleName="test-role",
    PolicyName="TerraformAdmin",
    PolicyDocument=json.dumps(expected_policy),
  )


def test_create_iam_role_other_error() -> None:
  mock_iam = MagicMock(spec=IAMClient)
  mock_iam.create_role.side_effect = ClientError(
    {
      "Error": {"Code": "ServiceFailure", "Message": "Internal error"},
      "ResponseMetadata": {
        "RequestId": "test-request",
        "HTTPStatusCode": 500,
        "HTTPHeaders": {},
        "RetryAttempts": 0,
        "HostId": "test-host",
      },
    },
    "CreateRole",
  )

  with pytest.raises(ValueError, match="Error creating IAM role test-role"):
    create_iam_role(mock_iam, "test-role", {"Version": "2012-10-17", "Statement": []})


def test_get_aws_org_accounts_error(mock_boto3: MagicMock) -> None:
  mock_org = mock_boto3("organizations")
  mock_org.get_paginator.side_effect = ClientError(
    {
      "Error": {"Code": "ServiceFailure", "Message": "Internal error"},
      "ResponseMetadata": {
        "RequestId": "test-request",
        "HTTPStatusCode": 500,
        "HTTPHeaders": {},
        "RetryAttempts": 0,
        "HostId": "test-host",
      },
    },
    "ListAccounts",
  )

  with pytest.raises(ValueError, match="Error retrieving accounts"):
    get_aws_org_accounts()


def test_main(mocker: MockerFixture, tmp_path: Path, test_data: dict[str, str]) -> None:
  mock_org_client = MagicMock()
  mock_org_client.get_paginator.return_value.paginate.return_value = [
    {
      "Accounts": [
        {"Name": "test-account", "Id": test_data["account_id"]},
      ]
    }
  ]

  mocker.patch("utils.config.ACCOUNTS_DIRECTORY_PATH", str(tmp_path))
  mocker.patch("boto3.client", return_value=mock_org_client)

  account_dir = tmp_path / "test-account"
  account_dir.mkdir()
  details_file = account_dir / "account_details.hcl"
  details_file.write_text('locals { account_id = "" }')

  mocker.patch("utils.parse_ous_accounts_data.get_management_account_details")
  mocker.patch("utils.parse_ous_accounts_data.get_terraform_backend_config")
  mocker.patch("setup_terraform_account_roles.create_terraform_admin_role")
  mocker.patch("setup_terraform_account_roles.terragrunt_init_account_dirs")

  main()
