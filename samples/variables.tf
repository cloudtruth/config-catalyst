variable "vpc_cidr_block" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr_block" {
  description = "Public subnet CIDR block"
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_cidr_block" {
  description = "Private subnet CIDR block"
  type        = string
  default     = "10.0.2.0/24"
}

variable "availability_zones" {
  description = "Availability zones (comma-separated list)"
  type        = string
  default     = "us-east-1a,us-east-1b"
}

variable "key_pair_name" {
  description = "Key pair name for SSH access"
  type        = string
  default     = "my-key-pair"
}

variable "instance_name" {
  description = "Name for the EC2 instance"
  type        = string
  default     = "my-app-server"
}

variable "instance_ami" {
  description = "Image ID for the EC2 instance (AMI)"
  type        = string
  default     = "ami-0123456789abcdef0"
}

variable "instance_type" {
  description = "Instance type for the EC2 instance"
  type        = string
  default     = "t2.micro"
}

variable "security_group_ids" {
  description = "Security group IDs for the EC2 instance (comma-separated list)"
  type        = string
  default     = "sg-12345678,sg-87654321"
}
