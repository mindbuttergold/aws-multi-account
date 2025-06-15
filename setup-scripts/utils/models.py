from pydantic import BaseModel, field_validator


class TerraformBackendConfig(BaseModel):
  aws_region: str
  terraform_admin_role_name: str
  s3_backend_bucket_name: str
  create_terraform_admin_role: bool
  create_s3_backend_bucket: bool

  @field_validator("aws_region")
  @classmethod
  def validate_region(cls, v: str) -> str:
    error_msg = "AWS_REGION cannot be empty"
    if not v:
      raise ValueError(error_msg)
    return v

  @field_validator("terraform_admin_role_name")
  @classmethod
  def validate_tf_role_name(cls, v: str) -> str:
    error_msg = "TERRAFORM_ADMIN_ROLE_NAME cannot be empty"
    if not v:
      raise ValueError(error_msg)
    return v

  @field_validator("s3_backend_bucket_name")
  @classmethod
  def validate_bucket_name(cls, v: str) -> str:
    error_msg = "S3_BACKEND_BUCKET_NAME cannot be empty"
    if not v:
      raise ValueError(error_msg)
    return v


class Account(BaseModel):
  name: str
  id: str
  organizational_unit: str
  terraform_backend_config: TerraformBackendConfig

  @field_validator("name")
  @classmethod
  def validate_name(cls, v: str) -> str:
    error_msg = "Account name cannot be empty"
    if not v:
      raise ValueError(error_msg)
    return v

  @field_validator("organizational_unit")
  @classmethod
  def validate_ou(cls, v: str) -> str:
    error_msg = "Organizational unit cannot be empty"
    if not v:
      raise ValueError(error_msg)
    return v


class ManagementAccountDetails(Account):
  name: str
  id: str
  email: str
  parent_ou_id: str

  @field_validator("name")
  @classmethod
  def validate_name(cls, v: str) -> str:
    error_msg = "Management account name cannot be empty"
    if not v:
      raise ValueError(error_msg)
    return v

  @field_validator("id")
  @classmethod
  def validate_id(cls, v: str) -> str:
    error_msg = "Management account ID cannot be empty"
    if not v:
      raise ValueError(error_msg)
    return v

  @field_validator("email")
  @classmethod
  def validate_email(cls, v: str) -> str:
    error_msg = "Management account email cannot be empty"
    if not v:
      raise ValueError(error_msg)
    return v

  @field_validator("parent_ou_id")
  @classmethod
  def validate_parent_ou(cls, v: str) -> str:
    error_msg = "Management account parent OU ID cannot be empty"
    if not v:
      raise ValueError(error_msg)
    return v
