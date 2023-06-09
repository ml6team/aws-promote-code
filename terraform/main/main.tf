/******************************************
  AWS provider configuration
 *****************************************/

provider "aws" {
  shared_config_files = var.enable_profile ? ["~/.aws/config"] : null
  profile             = var.enable_profile ? var.profile : null
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

variable "enable_profile" {
  description = "Enable to use AWS profile for authentication"
  type        = bool
  default     = false
}

/******************************************
  VPC configuration
 *****************************************/

module "vpc-network" {
  source = "../modules/vpc"
}
