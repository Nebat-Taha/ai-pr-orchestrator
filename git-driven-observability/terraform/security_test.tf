# Savi Finance - Infrastructure Test
# Contact: admin-devops@savi.com
# AWS Account: 123456789012

provider "aws" {
  region     = "us-east-1"
  access_key = "AKIAEXAMPLE123456789"
  secret_key = "SuperSecretKey/Value+12345"
}

resource "aws_instance" "bastion" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.medium"

  # Internal connection details
  private_ip = "10.50.1.102"

  user_data = <<-EOF
              #!/bin/bash
              # Setting up the ubuntu user for internal-db-01
              useradd -m ubuntu
              echo "ubuntu:SaviPassword2026!" | chpasswd
              EOF
}
