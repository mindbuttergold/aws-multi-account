ACCOUNTS_PREFIX = "test"
AWS_REGION = "us-west-2"
CREATE_TERRAFORM_ADMIN_ROLE = True
TERRAFORM_ADMIN_ROLE_NAME = "TerraformAdminRole"
CREATE_S3_BACKEND_BUCKET = True
S3_BACKEND_BUCKET_NAME = "test-terraform-state"
MANAGEMENT_ACCOUNT_NAME = "test-management"
MANAGEMENT_ACCOUNT_ID = "111111111111"
MANAGEMENT_ACCOUNT_EMAIL = "test@gmail.com"
PARENT_OU_ID = "r-test"

OUS_ACCOUNTS = {
  "Management": [
    {"name": f"{MANAGEMENT_ACCOUNT_NAME}", "id": MANAGEMENT_ACCOUNT_ID},
  ],
  "Infrastructure": [
    {"name": f"{ACCOUNTS_PREFIX}-backup", "id": "222222222222"},
    {"name": f"{ACCOUNTS_PREFIX}-infrastructure-production", "id": "333333333333"},
  ],
  "Workloads": [
    {"name": f"{ACCOUNTS_PREFIX}-workloads-production", "id": "444444444444"},
    {"name": f"{ACCOUNTS_PREFIX}-workloads-staging", "id": "555555555555"},
  ],
  "Sandbox": [
    {"name": f"{ACCOUNTS_PREFIX}-sandbox", "id": "666666666666"},
  ],
  "Security": [
    {"name": f"{ACCOUNTS_PREFIX}-security", "id": "777777777777"},
  ],
}
