locals {
  account_name              = "mbg-infrastructure-staging"
  account_id                = "555555555555"
  organizational_unit       = "Infrastructure"
  aws_region                = "us-west-2"
  terraform_admin_role_name = "TerraformAdminRole"
  s3_backend_bucket_name    = "mbg-terraform-state"
}