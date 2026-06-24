resource "aws_instance" "worker-node" {
  ami           = var.ami_id // Replace with actual AMI ID for EC2 worker node
  instance_type = var.ec2_instance_type // Define the desired AWS EC2 instance type here, e.g., 't2.micro' or 'c5d.large'
  
  vpc_security_group_ids = [var.vpc_sg_id] // Provide your VPC Security Group ID for this particular role to ensure proper security configuration and access controls within the AWS infrastructure

  tags {
    Name                        = "worker-node"
    Environment                = var.environment
    Project                     = var.project
    ManagedBy                   = "AI-Orchestrator"
    Jira_Automation             = true
    Terraform_Mandatory         = false // This tag indicates that the instance is managed by an orchestrator, but may not be required per organizational standards; consult with your infrastructure security guidelines. If it's mandatory in all AWS resources for auditing or compliance purposes, set this to 'true'.
  }
}