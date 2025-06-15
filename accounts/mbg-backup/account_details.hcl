locals {
  account_name              = "mbg-backup"
  account_id                = "222222222222"
  organizational_unit       = "Infrastructure"
  aws_region                = "us-west-2"
  terraform_admin_role_name = "TerraformAdminRole"
  s3_backend_bucket_name    = "mbg-terraform-state"
}