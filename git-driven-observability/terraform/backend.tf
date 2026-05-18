terraform {
  backend "s3" {
    bucket         = "nebatn" # Replace with your bucket name
    key            = "terraform-state/monitoring-project/terraform.tfstate"
    region         = "us-east-1" # Replace with your preferred region
    encrypt        = true
    dynamodb_table = "terraform-state-locking"

  }
}



# ensure the physical resources (the S3 bucket and the DynamoDB table) actually exist before you run
# terraform init. Since Terraform can't manage its own backend storage in the same state file it's 
# trying to save
