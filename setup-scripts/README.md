# Setup Scripts

Scripts to automate the process of setting up multi-account AWS infrastructure using Terraform and Terragrunt Infrastructure as Code (IaC). The scripts will help you create your account directories, respective configuration files, and minimal AWS resources.

> **Important**: These setup scripts are designed for creating new AWS accounts, and should only be used when starting with a single management account. They are not intended for modifying existing AWS multi-account structures.

## Prerequisites

### AWS Requirements

1. **Management AWS Account:**
   - You need a management AWS account that is already part of an AWS Organization called "Management"
   - See: [Creating an organization with AWS Organizations](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_org_create.html)

2. **AWS Credentials:**
   - You need a user or role that has admin-level permissions to your management accounts
   - You need credentials configured in your local terminal to login to your management account
   - For secure terminal login to AWS, it is highly recommended to use [aws-vault](https://github.com/99designs/aws-vault). This tool helps securely store and access AWS credentials.

### Local Requirements

1. **Development Tools:**
   - Python 3.10 or later
   - [Hatch](https://hatch.pypa.io/latest/install/) - For environment management
   - [Terraform](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli) - see the `root.hcl` file for the version used in this setup
   - [Terragrunt](https://terragrunt.gruntwork.io/docs/getting-started/install/#install-via-a-package-manager) - see the `root.hcl` file for the version used in this setup
 
## Step-by-Step Setup Process

> **Important**: These steps must be executed in the exact order listed below to ensure proper account setup.

### 1. Prepare Your Environment

1. Remove the existing `accounts` directory:
   ```zsh
   rm -rf accounts/
   ```
   This ensures a clean slate for your custom account structure.

2. Configure your account structure by modifying `ous_accounts_registry.py`:
   - Change all required values listed in the file
   - Review and adjust any other desired values

3. Set up your local development environment:
   ```zsh
   cd ./setup-scripts
   
   # Create and activate an environment with Hatch
   
   make env
   
   # Install required dependencies
   
   make install
   
   # Verify setup by ensuring linting checks and tests pass
   
   make lint
   make test
   ```

### 2. Create Your New Accounts and Related Resources

  *If not on a Mac, you may need to use `python` instead of `python3` for all commands*

1. **Generate Your Accounts Directory Structure:**
   ```zsh
   python3 setup_account_directories.py
   ```
   This step: 
   - Re-creates the accounts directory structure for your custom accounts
   - Creates initial Terraform/Terragrunt configuration files for each account

2. **Setup Your Terraform Backend:**
   ```zsh
   python3 setup_terraform_backend.py
   ```
   This step:
   - Creates an AWS S3 bucket in your management account for storing your Terraform state files and locks
   - Configures S3 state locking (note this is the modern best practice instead of DynamoDB state locking)
   - Creates a terraform admin IAM role in your management account for managing your AWS resources
   
3. **Create Your New AWS Organizations and Accounts:**  
   
   Move to your management account directory (replace with your management account name)
   ```zsh
   cd ../accounts/<your_management_account_name>

   terragrunt init

   terragrunt apply

   # Review the plan carefully before typing "yes" to apply.
   ```
   This step:
   - Creates your new AWS Organizations and all of your new AWS Accounts

### 3. Configure Access to Your New Accounts

1. **Set Up Cross-Account Access:**  
   
   Move back to the setup scripts directory
   ```zsh
   cd ../../setup-scripts

   python3 setup_terraform_account_roles.py
   ```
   This step:
   - Assumes the default `OrganizationAccountAccessRole` that is automatically created for each account, to access your newly created accounts
   - Creates a new terraform admin role in each account for ongoing management of each account's resources
   - At present, this creates admin roles with full access, but you can modify the admin policy in this script to scope down permissions based on your security requirements
   - Initializes the Terraform backend for each account

2. **Create Account Aliases for Each Account:**  
   
   Move to the accounts directory
   ```zsh
   cd ../accounts/

   # Warning: The command below will immediately apply the IAC to create an account alias for each account without showing the plan
   # The alias will be the same name as each account directory

   terragrunt run-all apply

   # If you prefer to see the plan first, you will need to go into each individual account directory one-by-one and run the following 

   terragrunt apply 
   ```
   This step:
   - Finalizes the setup by creating an account alias resource across all of your accounts. This allows you to login with a friendly-name instead of the account number.

## Final State

After completing these steps, you'll have:
- A properly structured AWS multi-account setup
- Secure state management using S3 backend and S3 locking
- Cross-account admin access roles for further Terraform/Terragrunt IAC operations. You can assume these roles to login to the individual accounts
- The account_details.hcl file in each account directory will list the account ID and other info for each account
- A foundation for adding additional AWS resources per account (can create modules and call them across accounts or create one-off terraform files inside specific account directories)

## Recommended Next Steps:
- Setup additional, non-admin roles that can be assumed to access the new accounts, via IAC
- Delete the setup-scripts directory and related Github Workflow, so that nothing is accidentally changed after setup
  