output "vpc_id" {
  value       = aws_vpc.this.id
  description = "The ID of the VPC for Security Group attachment"
}

output "public_subnet_id" {
  value       = aws_subnet.this.id
  description = "The ID of the subnet for EC2 placement"
}

output "vpc_cidr" {
  value       = aws_vpc.this.cidr_block
  description = "The CIDR block used for internal Security Group rules"
}
