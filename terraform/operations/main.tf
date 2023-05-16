/******************************************
  AWS provider configuration
 *****************************************/

provider "aws" {
  # region = var.region
  shared_config_files = ["~/.aws/config"]
  profile = "operations"
}

/******************************************
  Variables
 *****************************************/

variable "account" {
  description = "AWS account id"
  type        = string
}

variable "profile" {
  description = "AWS account profile name"
  type        = string
}

variable "region" {
  description = "Default AWS region for resources"
  type        = string
}

variable "dev_account_id" {
  description = "The account ID of the 'dev' account"
  type        = string
}

variable "staging_account_id" {
  description = "The account ID of the 'staging' account"
  type        = string
}

variable "prod_account_id" {
  description = "The account ID of the 'prod' account"
  type        = string
}

/******************************************
  VPC configuration
 *****************************************/

# module "vpc-network" {
#   source = "../modules/vpc"
# }
