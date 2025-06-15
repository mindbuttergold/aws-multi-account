locals {
  account_name              = "mbg-workloads-production"
  account_id                = "999999999999"
  organizational_unit       = "Workloads"
  aws_region                = "us-west-2"
  terraform_admin_role_name = "TerraformAdminRole"
  s3_backend_bucket_name    = "mbg-terraform-state"
}