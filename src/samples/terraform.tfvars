# Define variables for AWS infrastructure

# VPC CIDR block
vpc_cidr_block = "10.0.0.0/16"

# Public subnet CIDR block
public_subnet_cidr_block = "10.0.1.0/24"

# Private subnet CIDR block
private_subnet_cidr_block = "10.0.2.0/24"

# Availability zones (comma-separated list)
availability_zones = "us-east-1a,us-east-1b"

# Key pair name for SSH access
key_pair_name = "my-key-pair"

# Name for the EC2 instance
instance_name = "my-app-server"

# Image ID for the EC2 instance (AMI)
instance_ami = "ami-0123456789abcdef0"

# Instance type for the EC2 instance
instance_type = "t2.micro"

# Security group IDs for the EC2 instance (comma-separated list)
security_group_ids = "sg-12345678,sg-87654321"
