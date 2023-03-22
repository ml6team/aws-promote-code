/******************************************
  AWS provider configuration
 *****************************************/

provider "aws" {
  region = var.region
}

/******************************************
  Variables
 *****************************************/

variable "account" {
  description = "AWS account name"
  type        = string
}

variable "region" {
  description = "Default AWS region for resources"
  type        = string
}

/******************************************
  VPC configuration
 *****************************************/

module "vpc-network" {
  source = "../modules/vpc"
}
