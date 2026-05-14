# ==============================================================================
# ROOT MODULE: Git-Driven Monitoring Platform
# ARCHITECTURE: 
#   - Decoupled Networking, Security, Identity, and Compute.
#   - Deploys 1 Monitoring Engine and 1 Remote Test Node.
#   - Multi-tier deployment using reusable Compute and IAM modules.
#   - Orchestrates one 'Monitoring Server' and one 'Remote Node'.
#
# DECISIONS: 
#   - SECURITY: Define specific JSON policies here and pass them to the IAM module.
#   - AUTOMATION: Tags are used as the primary keys for Ansible Dynamic Inventory.
#   - REUSABILITY: Each instance call uses the same module but with different 'custom_tags'.
#   - MODULARITY: Every resource is called via a generic 'this' module.
#   - CONNECTIVITY: Uses 'public_ip' for GitHub Runner/Ansible access.
#   - SECURITY: Port 9090 is locked to 'var.my_ip' (GitHub Secret).
# ==============================================================================

# 1. --- NETWORK ---
# Creates the VPC, Subnet, and Internet Gateway.
module "vpc" {
  source             = "./modules/vpc"
  project_name       = var.project_name
  vpc_cidr           = "10.0.0.0/16"
  public_subnet_cidr = "10.0.1.0/24"
}

# 2. --- SECURITY (FIREWALL) ---
# Creates the Security Group rules using the admin's secret IP.
module "monitoring_sg" {
  source       = "./modules/security_groups"
  name         = "${var.project_name}-monitoring-sg"
  vpc_id       = module.vpc.vpc_id
  project_name = var.project_name
  my_ip        = var.my_ip # Injected via TF_VAR_my_ip secret
  vpc_cidr     = module.vpc.vpc_cidr
}

# 3. --- IDENTITY (IAM) ---
# Defines what the Monitoring Server can do in the AWS API.
module "iam_monitoring" {
  source       = "./modules/iam"
  project_name = var.project_name
  role_name    = "${var.project_name}-monitoring-role"

  # We combine the SQS permissions with the Instance Connect permission here.
  policy_json = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # Permission 1: Monitoring Data (SQS/CloudWatch)
      {
        Action = [
          "ec2:DescribeInstances", # <-- ADD THIS LINE
          "ec2:DescribeTags",      # <-- ADD THIS for tag filtering
          "sqs:GetQueueAttributes",
          "sqs:ListQueues",
          "s3:ListAllMyBuckets",  # List all buckets in the account
          "s3:ListBucket",        # List objects inside a specific bucket
          "s3:GetBucketLocation", # Required to know which region to query
          "s3:GetBucketTagging",  # Useful if your script filters by tags
          "s3:GetObject",         # Only if your script needs to read file content
          "cloudwatch:GetMetricData",
          "cloudwatch:ListMetrics"
        ]
        Effect   = "Allow"
        Resource = "*"
      },
      # Permission 2: Keyless SSH Access (EC2 Instance Connect)
      {
        Effect   = "Allow"
        Action   = "ec2-instance-connect:SendSSHPublicKey"
        Resource = "*"
        Condition = {
          StringEquals = {
            "ec2:osuser" = "ubuntu"
          }
        }
      }
    ]
  })
}

# 4. --- COMPUTE: MONITORING ENGINE ---
# This is your Prometheus/Grafana server.
module "ec2_prometheus" {
  source               = "./modules/ec2"
  project_name         = var.project_name
  instance_type        = "t2.micro"
  public_subnet_id     = module.vpc.public_subnet_id
  security_group_id    = module.monitoring_sg.id
  iam_instance_profile = module.iam_monitoring.instance_profile_name

  custom_tags = {
    Name             = "${var.project_name}-prometheus-engine"
    Role             = "monitoring-server"
    Monitoring_Stack = "prometheus"
  }
}

# 5. --- COMPUTE: REMOTE TEST NODE ---
# A second instance to prove the Ansible automation works on remote targets.
module "ec2_remote_node" {
  source            = "./modules/ec2"
  project_name      = var.project_name
  instance_type     = "t2.micro"
  public_subnet_id  = module.vpc.public_subnet_id
  security_group_id = module.monitoring_sg.id


  # This node doesn't need AWS API access
  iam_instance_profile = null

  custom_tags = {
    Name             = "${var.project_name}-test-node"
    Role             = "web-server"
    Monitoring_Stack = "prometheus"
  }
}
