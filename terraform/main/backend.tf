/******************************************
  Remote backend configuration
 *****************************************/

# setup of the backend s3 bucket that will keep the remote state

terraform {
  backend "s3" {
    bucket = "101436505502-terraform"
    key    = "terraform_state"
    region = "eu-west-3"
  }
}
