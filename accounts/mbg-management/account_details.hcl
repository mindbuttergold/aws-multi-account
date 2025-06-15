locals {
  account_name              = "mbg-management"
  account_id                = "111111111111"
  organizational_unit       = "Management"
  aws_region                = "us-west-2"
  terraform_admin_role_name = "TerraformAdminRole"
  s3_backend_bucket_name    = "mbg-terraform-state"
}