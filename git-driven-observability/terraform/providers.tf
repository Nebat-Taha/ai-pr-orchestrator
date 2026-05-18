# terraform/providers.tf

terraform {
  required_version = ">= 1.10.0" # Ensuring you stay on a modern version

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0" # Using the latest major version 6
    }
  }
}

provider "aws" {
  region = var.aws_region

  # Default Tags: This is a lifesaver for monitoring.
  # Every resource created (EC2, VPC, etc.) will automatically have these tags.
  default_tags {
    tags = {
      Project   = "git-driven-monitoring"
      ManagedBy = "terraform"
      Layer     = "infrastructure"
      Owner     = "nebatn"
    }
  }
}
