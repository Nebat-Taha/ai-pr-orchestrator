# ==============================================================================
# MODULE: VPC Networking (The "Pipe")
# ARCHITECTURE: Regional Network with a single Public Subnet & Internet Gateway.
# TRIGGER: Called by root main.tf to establish the base network.
# DECISIONS: 
#   - LEAN DESIGN: Removed Security Groups to allow for modular firewalling.
#   - CONNECTIVITY: Internet Gateway (IGW) and Route Table are required to 
#     ensure the Public Subnet can reach the GitHub Runner (and vice versa).
#   - DNS: 'enable_dns_hostnames' is required for internal AWS service resolution.
# ==============================================================================

# 1. THE VPC CONTAINER
resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name    = "${var.project_name}-vpc"
    Project = var.project_name
  }
}

# 2. THE PUBLIC SUBNET
resource "aws_subnet" "this" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnet_cidr
  map_public_ip_on_launch = true

  # Pick the first AZ in the region (e.g., us-east-1a)
  availability_zone = data.aws_availability_zones.available.names[0]

  tags = {
    Name    = "${var.project_name}-public-subnet"
    Project = var.project_name
  }
}

# 3. INTERNET GATEWAY
resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name    = "${var.project_name}-igw"
    Project = var.project_name
  }
}

# 4. ROUTE TABLE
resource "aws_route_table" "this" {
  vpc_id = aws_vpc.this.id

  # Routing all traffic (0.0.0.0/0) to the Internet Gateway
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = {
    Name    = "${var.project_name}-public-rt"
    Project = var.project_name
  }
}

# 5. SUBNET ASSOCIATION
resource "aws_route_table_association" "this" {
  subnet_id      = aws_subnet.this.id
  route_table_id = aws_route_table.this.id
}

# --- DATA SOURCES ---
data "aws_availability_zones" "available" {
  state = "available"
}
