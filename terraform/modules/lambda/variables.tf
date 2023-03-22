variable "lambda_function_image_uri" {
  type        = string
  description = "Docker image of lambda function"
}

variable "function_name" {
  type        = string
  description = "Name of the lambda function"
}

variable "trigger_bucket_name" {
  type        = string
  description = "Bucket name"
  default = "null"
}

variable "trigger_queue_arn" {
  type        = string
  description = "SQS ARN"
  default = "null"
}

variable "http_trigger" {
  type        = bool
  description = "Include setup of http trigger"
  default = false
}
