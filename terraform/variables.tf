# ==============================================================================
# ROOT VARIABLES: Global Project Configuration
# STRATEGY: Externalize all environment-specific values.
# DECISION: 'project_name' acts as the prefix for all resources to ensure 
#           uniqueness and organized billing/tagging in AWS.
# ==============================================================================

variable "project_name" {
  type        = string
  description = "The name of the project (e.g., 'git-driven-monitoring')"
  default     = "monitoring-system"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

# This is the variable fed by the GitHub Action secret 'TF_VAR_my_ip'
variable "my_ip" {
  type        = string
  description = "The public IP of the administrator for restricted access"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}
