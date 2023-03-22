variable "network_name" {
  description = "Name of the VPC network"
  type        = string
  default     = "main-network"
}

variable "subnetwork_name" {
  description = "Name of the subnetwork"
  type        = string
  default     = "subnetwork"
}

variable "vpc_cidr_block" {
  description = "IPv4 CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_prefix" {
  description = "Prefix for private subnetwork"
  type        = string
  default     = "private"
}

variable "public_prefix" {
  description = "Prefix for public subnetwork"
  type        = string
  default     = "public"
}

variable "availability_zones" {
  description = "Number of availability zones"
  type        = number
  default     = 1

  validation {
    condition     = var.availability_zones >= 1
    error_message = "The number of availability zones should be at least 1."
  }

  validation {
    condition     = var.availability_zones <= 3
    error_message = "More than 3 availability zones is not recommended."
  }
}
