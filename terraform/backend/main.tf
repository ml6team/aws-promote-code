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
	AWS provider configuration
 *****************************************/

provider "aws" {
  region = var.region
}

/******************************************
  State storage configuration
 *****************************************/

resource "aws_s3_bucket" "terraform_state" {
  bucket = "${var.account}-terraform"
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}
