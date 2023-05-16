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

/******************************************
	AWS provider configuration
 *****************************************/

provider "aws" {
  shared_config_files = ["~/.aws/config"]
  profile = "operations"
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

    # dev
    principals {
      type        = "AWS"
      identifiers = ["157261447749"]
    }

    # staging
    principals {
      type        = "AWS"
      identifiers = ["381667332649"]
    }

    # prod
    principals {
      type        = "AWS"
      identifiers = ["343975642840"]
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
