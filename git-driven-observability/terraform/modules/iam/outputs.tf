# ==============================================================================
# OUTPUTS: Essential for passing the profile name to the EC2 module
# ==============================================================================

output "instance_profile_name" {
  value       = aws_iam_instance_profile.this.name
  description = "The name of the instance profile to be used in the EC2 module."
}
