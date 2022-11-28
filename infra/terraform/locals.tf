variable "yaml_config" {
  type = string
}

locals {
  variable = yamldecode(file("../config/${var.yaml_config}"))
}