/******************************************
  AWS provider configuration
 *****************************************/

provider "aws" { # default profile/alias
  shared_config_files = ["~/.aws/config"]
  profile             = "operations"
  region              = var.region
}

# access to other accounts

provider "aws" {
  alias               = "dev"
  shared_config_files = ["~/.aws/config"]
  profile             = "dev"
  region              = var.region
}

provider "aws" {
  alias               = "staging"
  shared_config_files = ["~/.aws/config"]
  profile             = "staging"
  region              = var.region
}

provider "aws" {
  alias               = "prod"
  shared_config_files = ["~/.aws/config"]
  profile             = "prod"
  region              = var.region
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
  OpenID Connect Provider (provides GitHub actions access)
 *****************************************/

module "openid_github_iam_operations" {
  source  = "../modules/openid_github_provider"
  account = var.account
}

module "openid_github_iam_dev" {
  source  = "../modules/openid_github_provider"
  account = var.dev_account_id
  providers = {
    aws = aws.dev
  }
}

module "openid_github_iam_staging" {
  source  = "../modules/openid_github_provider"
  account = var.staging_account_id
  providers = {
    aws = aws.staging
  }
}

module "openid_github_iam_prod" {
  source  = "../modules/openid_github_provider"
  account = var.prod_account_id
  providers = {
    aws = aws.prod
  }
}
