# ==============================================================================
# ARCHITECTURE: Generic EC2 Instance
# TRIGGER: Called by root main.tf for both Monitoring Server and Remote Nodes.
# DECISIONS: 
#   - Use Ubuntu 24.04 Noble for modern package support.
#   - 'ignore_changes' on AMI to prevent accidental destruction during routine runs.
#   - Root volume set to GP3 for better price/performance ratio.
# ==============================================================================

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
}

resource "aws_instance" "this" {
  # We renamed the resource from 'prometheus_server' to 'this' 
  # because this module now represents any generic instance.

  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = var.public_subnet_id
  vpc_security_group_ids = [var.security_group_id]


  # Only attaches the profile if one is provided
  iam_instance_profile = var.iam_instance_profile

  lifecycle {
    # Safety switch: prevent replacement if a new AMI version is released
    ignore_changes = [ami]
  }

  # MERGE STRATEGY: 
  # We combine the project name with the custom tags passed from the root.
  tags = merge(
    {
      Project = var.project_name
    },
    var.custom_tags
  )

  root_block_device {
    volume_size = 8
    volume_type = "gp3" # TODO : follow-up
  }
}

output "instance_ip" {
  value       = aws_instance.this.public_ip
  description = "Public IP for Ansible connectivity"
}
