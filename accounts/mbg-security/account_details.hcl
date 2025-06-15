locals {
  account_name              = "mbg-security"
  account_id                = "777777777777"
  organizational_unit       = "Security"
  aws_region                = "us-west-2"
  terraform_admin_role_name = "TerraformAdminRole"
  s3_backend_bucket_name    = "mbg-terraform-state"
}