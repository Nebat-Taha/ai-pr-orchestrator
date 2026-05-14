# terraform/outputs.tf

output "vpc_id" {
  value       = module.vpc.vpc_id
  description = "The ID of the VPC"
}

output "public_subnet_id" {
  description = "The ID of the public subnet"
  value       = module.vpc.public_subnet_id
}

output "prometheus_public_ip" {
  value = module.ec2_prometheus.instance_public_ip
}

output "remote_node_public_ip" {
  value = module.ec2_remote_node.instance_public_ip
}

