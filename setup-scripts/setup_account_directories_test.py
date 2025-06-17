# ignoring redefinition of pytest fixture functions
# ruff: noqa: F811

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from setup_account_directories import (
  create_account_terragrunt_files,
  main,
  setup_account_directory,
  setup_all_account_directories,
)

# ignoring unused imports from conftest, injected via fixtures
from tests.conftest import (  # noqa: F401
  account_details_content,
  terraform_config,
  terragrunt_content,
  test_account,
  test_account_data,
  test_account_factory,
  test_accounts,
  test_data,
)
from utils.models import Account, TerraformBackendConfig

FILES_PER_ACCOUNT = 2


def test_create_terragrunt_files(
  tmp_path: Path,
  mocker: MockerFixture,
  test_account_data: dict[str, str],
  account_details_content: str,
  terragrunt_content: str,
) -> None:
  mock_write = mocker.patch("utils.file_ops.write_account_file")
  create_account_terragrunt_files(str(tmp_path), **test_account_data)

  assert mock_write.call_count == FILES_PER_ACCOUNT
  expected_files = {
    "account_details.hcl": account_details_content,
    "terragrunt.hcl": terragrunt_content,
  }

  for filename, expected_content in expected_files.items():
    mock_write.assert_has_calls(
      [
        mocker.call(
          str(Path(tmp_path) / filename),
          expected_content.strip() + "\n",
          filename,
          test_account_data["account_name"],
        )
      ]
    )


def test_directory_errors(tmp_path: Path, test_account: Account, mocker: MockerFixture) -> None:
  mocker.patch("utils.file_ops.create_directory", side_effect=OSError("Permission denied"))
  with pytest.raises(OSError, match="Permission denied"):
    setup_account_directory(test_account, str(tmp_path))

  mocker.patch(
    "utils.file_ops.create_directory",
    return_value=None,
  )
  mocker.patch("utils.file_ops.write_account_file", side_effect=OSError("Disk full"))
  with pytest.raises(OSError, match="Disk full"):
    setup_account_directory(test_account, str(tmp_path))


def test_invalid_configs(terraform_config: TerraformBackendConfig) -> None:
  test_cases = [
    ("aws_region", "", "AWS_REGION cannot be empty"),
    ("terraform_admin_role_name", "", "TERRAFORM_ADMIN_ROLE_NAME cannot be empty"),
    ("s3_backend_bucket_name", "", "S3_BACKEND_BUCKET_NAME cannot be empty"),
  ]

  for field, value, error in test_cases:
    with pytest.raises(ValueError, match=error):
      TerraformBackendConfig(
        aws_region=terraform_config.aws_region if field != "aws_region" else value,
        terraform_admin_role_name=terraform_config.terraform_admin_role_name
        if field != "terraform_admin_role_name"
        else value,
        s3_backend_bucket_name=terraform_config.s3_backend_bucket_name if field != "s3_backend_bucket_name" else value,
        create_terraform_admin_role=True,
        create_s3_backend_bucket=True,
      )


def test_end_to_end_setup(tmp_path: Path, mocker: MockerFixture, test_accounts: list[Account]) -> None:
  mocker.patch("utils.config.ACCOUNTS_DIRECTORY_PATH", str(tmp_path))
  mock_dir = mocker.patch("utils.file_ops.create_directory")
  mock_write = mocker.patch("utils.file_ops.write_account_file")

  setup_all_account_directories(test_accounts)

  mock_dir.assert_has_calls([mocker.call(str(tmp_path))])
  for account in test_accounts:
    mock_dir.assert_has_calls([mocker.call(str(Path(tmp_path) / account.name))])
  assert mock_dir.call_count == len(test_accounts) + 1

  assert mock_write.call_count == len(test_accounts) * FILES_PER_ACCOUNT

  for account in test_accounts:
    calls = [call for call in mock_write.call_args_list if account.name in str(call[0][0])]
    assert len(calls) == FILES_PER_ACCOUNT


def test_missing_backend_config(tmp_path: Path, test_account: Account) -> None:
  test_account_no_backend = Account.model_construct(
    id=test_account.id,
    name=test_account.name,
    organizational_unit=test_account.organizational_unit,
    terraform_backend_config=None,
  )
  with pytest.raises(
    ValueError,
    match=f"Account {test_account.name} is missing required terraform_backend_config",
  ):
    setup_account_directory(test_account_no_backend, str(tmp_path))


def test_setup_all_account_directories_empty(tmp_path: Path, mocker: MockerFixture) -> None:
  mocker.patch("utils.config.ACCOUNTS_DIRECTORY_PATH", str(tmp_path))
  setup_all_account_directories([])
  assert Path(tmp_path).exists()


def test_main_function(mocker: MockerFixture) -> None:
  mock_get_data = mocker.patch("setup_account_directories.parse_ous_accounts_data.get_accounts_data")
  mock_setup = mocker.patch("setup_account_directories.setup_all_account_directories")
  mock_get_data.return_value = []

  main()

  mock_get_data.assert_called_once_with()
  mock_setup.assert_called_once_with([])
