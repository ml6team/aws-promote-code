/******************************************
  AWS provider configuration
 *****************************************/

provider "aws" {
  shared_config_files = ["~/.aws/config"]
  profile             = var.profile
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

variable "scheduled_pipeline_run" {
  description = "Enables scheduled run of SageMaker Pipeline"
  type        = string
}

/******************************************
  VPC configuration
 *****************************************/

module "vpc-network" {
  source = "../modules/vpc"
}
