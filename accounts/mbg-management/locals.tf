locals {
  parent_ou_id             = "r-test"
  management_account_email = "test@gmail.com"
  organizational_units     = ["Infrastructure", "Management", "Sandbox", "Security", "Workloads"]
  accounts = [
    {
      "name" : "mbg-management",
      "organizational_unit" : "Management"
    },
    {
      "name" : "mbg-backup",
      "organizational_unit" : "Infrastructure"
    },
    {
      "name" : "mbg-infrastructure-production",
      "organizational_unit" : "Infrastructure"
    },
    {
      "name" : "mbg-infrastructure-staging",
      "organizational_unit" : "Infrastructure"
    },
    {
      "name" : "mbg-infrastructure-development",
      "organizational_unit" : "Infrastructure"
    },
    {
      "name" : "mbg-workloads-production",
      "organizational_unit" : "Workloads"
    },
    {
      "name" : "mbg-workloads-staging",
      "organizational_unit" : "Workloads"
    },
    {
      "name" : "mbg-workloads-development",
      "organizational_unit" : "Workloads"
    },
    {
      "name" : "mbg-sandbox",
      "organizational_unit" : "Sandbox"
    },
    {
      "name" : "mbg-security",
      "organizational_unit" : "Security"
    }
  ]
}
