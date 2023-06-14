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
	AWS provider configuration
 *****************************************/

provider "aws" {
  shared_config_files = ["~/.aws/config"]
  profile             = "operations"
}

/******************************************
  State storage configuration
 *****************************************/

resource "aws_s3_bucket" "terraform_state" {
  bucket = "${var.account}-${var.profile}-terraform"
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

/******************************************
  Access to the Terraform backend from other accounts
 *****************************************/

resource "aws_s3_bucket_policy" "allow_access_from_another_account" {
  bucket = aws_s3_bucket.terraform_state.id
  policy = data.aws_iam_policy_document.allow_access_from_another_account.json
}

data "aws_iam_policy_document" "allow_access_from_another_account" {
  statement {
    principals {
      type = "AWS"
      identifiers = [
        var.dev_account_id,     # dev
        var.staging_account_id, # staging
        var.prod_account_id,    # prod
      ]
    }
    actions = [
      "*"
    ]
    resources = [
      aws_s3_bucket.terraform_state.arn,
      "${aws_s3_bucket.terraform_state.arn}/*",
    ]
  }
}
