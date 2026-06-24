resource "aws_instance" "example" {
  ami           = var.ami
  instance_type = var.instance_type

  tags = {
    Name        = var.name
    Project     = "Jira-Automation"
    ManagedBy   = "AI-Orchestrator"
  }
}
