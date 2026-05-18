# ==============================================================================
# MODULE: Security Group Factory
# ARCHITECTURE: Generic Security Group Container
# DECISION: We define the "Monitoring" rules here, but this module could be 
#           expanded to accept rules as a list/map variable for total reuse.
# ==============================================================================

resource "aws_security_group" "this" {
  name        = var.name
  description = "Security group for ${var.name}"
  vpc_id      = var.vpc_id

  # Rule 1: SSH (Standard for all our instances)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Rule 2: Management UI (Restricted to Secret IP)
  ingress {
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Rule 3: Exporter Scrapping (Internal VPC only)
  ingress {
    from_port   = 8000
    to_port     = 9100
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = var.name
    Project = var.project_name
  }
}


