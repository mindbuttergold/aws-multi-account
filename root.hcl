locals {
  terraform_version  = "~> 1.12.2"
  terragrunt_version = "~> 0.81.6"

  account_details = read_terragrunt_config("${get_terragrunt_dir()}/account_details.hcl")
  versions        = read_terragrunt_config(find_in_parent_folders("versions.hcl"))

  account_name              = local.account_details.locals.account_name
  account_id                = local.account_details.locals.account_id
  aws_region                = local.account_details.locals.aws_region
  organizational_unit       = local.account_details.locals.organizational_unit
  terraform_admin_role_name = local.account_details.locals.terraform_admin_role_name
  s3_backend_bucket_name    = local.account_details.locals.s3_backend_bucket_name
}

inputs = {
  account_name = local.account_name
}

generate "variables" {
  path      = "variables.tf"
  if_exists = "overwrite"
  contents  = <<EOF
variable "account_name" {
  description = "The name of the AWS account."
  type        = string
}
EOF
}

generate "provider" {
  path      = "provider.tf"
  if_exists = "overwrite"
  contents  = <<EOF
terraform {
  required_version = "${local.terraform_version}"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }

  backend "s3" {
    bucket  = "${local.s3_backend_bucket_name}"
    use_lockfile = true
    key     = "${path_relative_to_include()}/terraform.tfstate"
    region  = "${local.aws_region}"
    encrypt = true
  }
}

provider "aws" {
  region = "${local.aws_region}"

  assume_role {
    role_arn     = "arn:aws:iam::${local.account_id}:role/${local.terraform_admin_role_name}"
    session_name = "terraform-session"
  }
}
EOF
}

generate "main" {
  path      = "main.tf"
  if_exists = "overwrite"
  contents  = <<EOF
resource "aws_iam_account_alias" "alias" {
  account_alias = var.account_name
}
EOF
}
