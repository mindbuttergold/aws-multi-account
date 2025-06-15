resource "aws_organizations_organizational_unit" "managed" {
  for_each  = toset(local.organizational_units)
  name      = each.value
  parent_id = local.parent_ou_id
}

resource "aws_organizations_account" "managed" {
  for_each = {
    for account in local.accounts :
    account.name => account
    if account.organizational_unit != "Management"
  }
  name      = each.value.name
  email     = replace(local.management_account_email, "@", "+${each.value.name}@")
  parent_id = aws_organizations_organizational_unit.managed[each.value.organizational_unit].id
}
