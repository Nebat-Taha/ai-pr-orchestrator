# ==============================================================================
# MODULE OUTPUT: Security Group
# DECISION: Export the ID so it can be 'injected' into the EC2 module.
# ==============================================================================

output "id" {
  value       = aws_security_group.this.id
  description = "The ID of the security group."
}
