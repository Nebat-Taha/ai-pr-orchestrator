# variables.tf
# ==============================================================================
# MODULE: IAM Identity Factory
# STRATEGY: Decoupled Permissions
# DECISION: The module creates the "Identity" (Role + Profile), but the 
#           specific "Permissions" (Policy JSON) are passed in as a variable.
# ==============================================================================

variable "role_name" {
  type        = string
  description = "The name of the IAM role (e.g., prometheus-monitoring-role)"
}

variable "policy_json" {
  type        = string
  description = "The JSON-encoded IAM policy document defining what this role can do."
}

variable "project_name" {
  type = string
}
