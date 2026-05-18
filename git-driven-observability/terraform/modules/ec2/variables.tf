# ==============================================================================
# MODULE: EC2 Compute
# STRATEGY: Reusable Blueprint
# DECISION: This module must not define "What" is being built, only "How" it is built.
#           All identity-specific data (Tags, Size, IAM) must be passed as variables.
# ==============================================================================

variable "project_name" {
  type        = string
  description = "The prefix used for naming resources"
}

variable "instance_type" {
  type        = string
  description = "EC2 instance size (e.g., t2.micro, t3.small)"
}

variable "public_subnet_id" {
  type = string
}

variable "security_group_id" {
  type = string
}


variable "iam_instance_profile" {
  type        = string
  description = "The IAM instance profile name. Pass null or empty string if not needed."
  default     = null
}

variable "custom_tags" {
  type        = map(string)
  description = "Map of tags to apply to the instance. Essential for Ansible Dynamic Inventory."
}
