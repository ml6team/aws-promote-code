# TODO: deploy in "operations" account
resource "aws_s3_bucket" "pipeline_registry" {
  bucket = "pipeline-registry-bucket"
  #   tags = {
  #   Name        = "My bucket"
  #   Environment = "Dev"
  # }
}