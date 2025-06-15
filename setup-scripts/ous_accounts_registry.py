# ----- MODIFY THE VALUES BELOW -----

# Replace with a prefix that will be used for your accounts
# This is to ensure your account names are standardized with unique aliases (AWS requires aliased to be globally unique)
ACCOUNTS_PREFIX = "mbg"
# Replace with your desired AWS region for all accounts
# should be the same region as the management account
AWS_REGION = "us-west-2"
# Set to True to create a new Terraform admin role in the management account
# If False, ensure your existing role has AWS admin permissions
CREATE_TERRAFORM_ADMIN_ROLE = True
# If create_terraform_admin_role is False, be sure to replace with an existing role name
TERRAFORM_ADMIN_ROLE_NAME = "TerraformAdminRole"
# Set to False if you have an existing s3 backend bucket you want to use
CREATE_S3_BACKEND_BUCKET = True
# Replace if you have an existing s3 backend bucket
S3_BACKEND_BUCKET_NAME = f"{ACCOUNTS_PREFIX}-terraform-state"
# Replace with your existing management account name
MANAGEMENT_ACCOUNT_NAME = "mbg-management"
# Replace with your management account ID
MANAGEMENT_ACCOUNT_ID = "111111111111"
# Replace with the email address associated with your management account
MANAGEMENT_ACCOUNT_EMAIL = "test@gmail.com"
# Replace with the Root OU ID of your management account
PARENT_OU_ID = "r-test"

# ----- END REQUIRED MODIFICATIONS -----

# The accounts below, except for the management account, will be created through the setup process
# All account IDs will be populated in each account directory's accounts_details.hcl file after creation

# You may modify / add / remove accounts if desired
# note that AWS has a limit of 10 total accounts per OU unless you request a limit increase
# If you delete/close accounts, those persist for quite a while and still count towards the limit

OUS_ACCOUNTS = {
  # The management account must be in the Management OU
  "Management": [
    {"name": f"{MANAGEMENT_ACCOUNT_NAME}", "id": MANAGEMENT_ACCOUNT_ID},
  ],
  # You may change the names of the other OUs and account suffixes
  "Infrastructure": [
    {"name": f"{ACCOUNTS_PREFIX}-backup", "id": ""},
    {"name": f"{ACCOUNTS_PREFIX}-infrastructure-production", "id": ""},
    {"name": f"{ACCOUNTS_PREFIX}-infrastructure-staging", "id": ""},
    {"name": f"{ACCOUNTS_PREFIX}-infrastructure-development", "id": ""},
  ],
  "Workloads": [
    {"name": f"{ACCOUNTS_PREFIX}-workloads-production", "id": ""},
    {"name": f"{ACCOUNTS_PREFIX}-workloads-staging", "id": ""},
    {"name": f"{ACCOUNTS_PREFIX}-workloads-development", "id": ""},
  ],
  "Sandbox": [
    {"name": f"{ACCOUNTS_PREFIX}-sandbox", "id": ""},
  ],
  "Security": [
    {"name": f"{ACCOUNTS_PREFIX}-security", "id": ""},
  ],
}
