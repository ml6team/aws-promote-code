#################################################
# Service quotas to run SageMaker Pipeline with GPU instances type
#################################################

# ml.g4dn.xlarge for training job usage
resource "aws_servicequotas_service_quota" "quota_sagemaker_training_job" {
  quota_code   = "L-3F53BF0F"
  service_code = "sagemaker"
  value        = 1
}

# ml.g4dn.xlarge for processing job usage
resource "aws_servicequotas_service_quota" "quota_sagemaker_procesing_job" {
  quota_code   = "L-2F1EB012"
  service_code = "sagemaker"
  value        = 1
}

# ml.g4dn.xlarge for transform job usage
resource "aws_servicequotas_service_quota" "quota_sagemaker_transform_job" {
  quota_code   = "L-4C5C5CA8"
  service_code = "sagemaker"
  value        = 2
}
