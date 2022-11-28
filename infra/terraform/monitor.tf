resource "azurerm_monitor_action_group" "action_groups" {
  for_each            = {for action_group in local.variable["action_groups"] : lower(action_group.type) == "email" ? action_group.name : null => action_group}
  name                = each.value.name
  resource_group_name = azurerm_resource_group.admin[0].name
  short_name          = each.value.short_name

  email_receiver {
    name          = each.value.name
    email_address = each.value.email_address
  }
}