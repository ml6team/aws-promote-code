/******************************************
  Remote backend configuration
 *****************************************/

# setup of the backend s3 bucket that will keep the remote state

terraform {
  backend "s3" {
    bucket = "123971416876-operations-terraform" 
    key    = "terraform_state_operations"
    region = "eu-west-3"
    profile = "operations"
  }
}
