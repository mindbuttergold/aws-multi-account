# aws-multi-account

[![CodeQL](https://github.com/mindbuttergold/template-repo/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/mindbuttergold/aws-multi-account/actions/workflows/github-code-scanning/codeql) [![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/mindbuttergold/aws-multi-account/badge)](https://scorecard.dev/viewer/?uri=github.com/mindbuttergold/aws-multi-account) [![OpenSSF Best Practices](https://www.bestpractices.dev/projects/10740/badge)](https://www.bestpractices.dev/projects/10740)

This repository demonstrates the setup of an AWS multi-account model with recommended Organization Units, via Infrastructure as Code (IAC) via Terraform and Terragrunt.

The `./accounts` directory and files at the root of the repository show the core infrastructure setup. 

The code in the `./setup-scripts` directory is just to facilitate custom, automated setup of the accounts directories and required IAM resources if desired. This `./setup-scripts` directory can be deleted if desired, and the infra setup will stand on its own with its own workflow, tests, etc.

## Organization Structure

```
AWS Organization Root
│
├── Management OU
│   └── Management Account (mbg-management)
│       └── Organization-wide IAM and account management
│
├── Security OU
│   └── Security Account (mbg-security)
│       └── Security tools, GuardDuty, audit logs
│
├── Infrastructure OU
│   ├── Backup Account (mbg-backup)
│   │   └── Centralized backup and disaster recovery
│   ├── Development Account (mbg-infrastructure-development)
│   │   └── Shared development infrastructure
│   ├── Staging Account (mbg-infrastructure-staging)
│   │   └── Pre-production infrastructure validation
│   └── Production Account (mbg-infrastructure-production)
│       └── Production infrastructure and shared services
│
├── Workloads OU
│   ├── Development Account (mbg-workloads-development)
│   │   └── Development environment workloads
│   ├── Staging Account (mbg-workloads-staging)
│   │   └── Pre-production workload validation
│   └── Production Account (mbg-workloads-production)
│       └── Production workloads and applications
│
└── Sandbox OU
    └── Sandbox Account (mbg-sandbox)
        └── Isolated environment for testing and exploration
```

This structure follows AWS best practices by separating accounts by their unique purposes, to isolate potential impact of security events. The infrastructure setup also employs role-based access control (RBAC) for cross-account login and resource management via IAC.

## AWS Documentation:

- [Benefits of Using Multiple AWS Accounts](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/benefits-of-using-multiple-aws-accounts.html)
- [Benefits of Using Organizational Units](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/benefits-of-using-organizational-units-ous.html)
- [Best Practices for a Multi-Account Environment](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices.html)
- [Organizing Your AWS Environment Using Multiple Accounts](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/organizing-your-aws-environment.html)
- [Design Principles for Your Multi-Account Strategy](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/design-principles-for-your-multi-account-strategy.html)
- [Recommended OUs and Accounts](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/recommended-ous-and-accounts.html)
- [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html)

## Getting Started

If you wish, you can use the setup scripts in this repository to create your own, custom AWS multi-account infrastructure. To do so, carefully follow all steps in the [setup-scripts README](./setup-scripts/README.md).

## Testing

There are basic unit tests that validate the structure and configuration of the AWS multi-account infrastructure setup, without requiring actual AWS credentials or resources.

### Test Dependencies:
   - Python 3.10 or later
   - [Hatch](https://hatch.pypa.io/latest/install/) - For environment management
   - All other deps are the `requirements.lock` file.

### Running Tests

A Makefile is available for easier local development, most of which just uses Hatch scripts from the `pyproject.yaml` file.
You can choose to use the makefile commands, or you can use the Hatch script commands directly that are noted in the Makefile.

```zsh
# Create and activate a virtual Hatch environment

make env

# Install the required dependencies

make install

# Run tests

make test

# Run linting

make lint
```

## Cost

This setup should not incur costs to use. AWS does not charge you for creating Organizational Units or accounts. Rather, you incur charges based on resources used within accounts.

The setup scripts will create an S3 bucket and IAM roles, which should fall within the free-tier level. 

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
