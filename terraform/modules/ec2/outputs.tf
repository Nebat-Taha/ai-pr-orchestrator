# ==============================================================================
# MODULE OUTPUT: EC2 Instance
# DECISION: We export the public IP so the Root can aggregate it for Ansible.
# ==============================================================================

output "instance_public_ip" {
  value       = aws_instance.this.public_ip
  description = "The public IP address of the EC2 instance."
}
