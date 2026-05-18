# ==============================================================================
# ARCHITECTURE: IAM Role & Instance Profile
# TRIGGER: Called by root main.tf to provide EC2 instances with AWS API access.
# DECISIONS: 
#   - Use 'this' naming convention to keep the module generic.
#   - Create an 'Instance Profile' because that is the actual container 
#     the EC2 instance "plugs into" to inherit the Role.
# ==============================================================================

resource "aws_iam_role" "this" {
  name = var.role_name

  # The "Trust Policy" - allows EC2 service to assume this role
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name    = var.role_name
    Project = var.project_name
  }
}

# The Policy itself (the specific permissions)
resource "aws_iam_policy" "this" {
  name        = "${var.role_name}-policy"
  description = "Policy for ${var.role_name}"
  policy      = var.policy_json
}

# Attach the policy to the role
resource "aws_iam_role_policy_attachment" "this" {
  role       = aws_iam_role.this.name
  policy_arn = aws_iam_policy.this.arn
}

# The Instance Profile (The part the EC2 actually sees)
resource "aws_iam_instance_profile" "this" {
  name = "${var.role_name}-profile"
  role = aws_iam_role.this.name
}

