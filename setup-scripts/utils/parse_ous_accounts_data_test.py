import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
from pytest_mock import MockerFixture

from tests.conftest import TEST_ACCOUNT_COUNT
from utils.models import Account, ManagementAccountDetails, TerraformBackendConfig
from utils.parse_ous_accounts_data import (
  get_accounts_data,
  get_management_account_details,
  get_terraform_backend_config,
  load_ous_accounts_data,
  ous_accounts_data,
)


def load_test_registry_data() -> ModuleType:
  test_registry_path = Path(__file__).parent.parent / "tests" / "test_ous_accounts_registry.py"
  spec = importlib.util.spec_from_file_location("test_registry", test_registry_path)
  if spec is None:
    msg = f"Could not load spec from {test_registry_path}"
    raise ImportError(msg)

  test_registry = importlib.util.module_from_spec(spec)
  if spec.loader is None:
    msg = "Module spec has no loader"
    raise ImportError(msg)

  spec.loader.exec_module(test_registry)
  return test_registry


TEST_REGISTRY = load_test_registry_data()


@pytest.fixture
def test_registry_path() -> Path:
  return Path(__file__).parent.parent / "tests" / "test_ous_accounts_registry.py"


@pytest.fixture(autouse=True)
def mock_config_path(mocker: MockerFixture, test_registry_path: Path) -> None:
  mocker.patch("utils.parse_ous_accounts_data.OUS_ACCOUNTS_REGISTRY_PATH", str(test_registry_path))


def test_load_ous_accounts_data() -> None:
  result = load_ous_accounts_data()

  assert result is not None
  assert "OUS_ACCOUNTS" in result

  assert result["AWS_REGION"] == TEST_REGISTRY.AWS_REGION
  assert result["MANAGEMENT_ACCOUNT_ID"] == TEST_REGISTRY.MANAGEMENT_ACCOUNT_ID
  assert result["MANAGEMENT_ACCOUNT_EMAIL"] == TEST_REGISTRY.MANAGEMENT_ACCOUNT_EMAIL
  assert result["PARENT_OU_ID"] == TEST_REGISTRY.PARENT_OU_ID


def test_ous_accounts_data() -> None:
  result = ous_accounts_data()

  assert isinstance(result, dict)
  assert "accounts_data" in result
  assert len(result["accounts_data"]) == TEST_ACCOUNT_COUNT

  accounts_data = result["accounts_data"]
  for account in accounts_data:
    assert isinstance(account, Account)
    assert account.name.startswith(TEST_REGISTRY.ACCOUNTS_PREFIX)
    assert account.id != ""
    assert account.organizational_unit in [
      "Management",
      "Infrastructure",
      "Workloads",
      "Sandbox",
      "Security",
    ]


def test_get_accounts_data() -> None:
  accounts = get_accounts_data()

  assert isinstance(accounts, list)
  assert len(accounts) == TEST_ACCOUNT_COUNT

  management_account = next(
    (acc for acc in accounts if acc.name == f"{TEST_REGISTRY.ACCOUNTS_PREFIX}-management"),
    None,
  )
  assert management_account is not None
  assert management_account.id == TEST_REGISTRY.MANAGEMENT_ACCOUNT_ID
  assert management_account.organizational_unit == "Management"

  infra_account = next(
    (acc for acc in accounts if acc.name == f"{TEST_REGISTRY.ACCOUNTS_PREFIX}-infrastructure-production"),
    None,
  )
  assert infra_account is not None
  assert infra_account.id == TEST_REGISTRY.OUS_ACCOUNTS["Infrastructure"][1]["id"]
  assert infra_account.organizational_unit == "Infrastructure"


def test_get_terraform_backend_config() -> None:
  result = get_terraform_backend_config()

  assert isinstance(result, TerraformBackendConfig)
  assert result.aws_region == TEST_REGISTRY.AWS_REGION
  assert result.terraform_admin_role_name == TEST_REGISTRY.TERRAFORM_ADMIN_ROLE_NAME
  assert result.s3_backend_bucket_name == TEST_REGISTRY.S3_BACKEND_BUCKET_NAME
  assert result.create_terraform_admin_role == TEST_REGISTRY.CREATE_TERRAFORM_ADMIN_ROLE
  assert result.create_s3_backend_bucket == TEST_REGISTRY.CREATE_S3_BACKEND_BUCKET


def test_get_management_account_details() -> None:
  result = get_management_account_details()

  assert isinstance(result, ManagementAccountDetails)
  assert result.id == TEST_REGISTRY.MANAGEMENT_ACCOUNT_ID
  assert result.email == TEST_REGISTRY.MANAGEMENT_ACCOUNT_EMAIL
  assert result.parent_ou_id == TEST_REGISTRY.PARENT_OU_ID
  assert result.name == f"{TEST_REGISTRY.ACCOUNTS_PREFIX}-management"
  assert result.organizational_unit == "Management"
