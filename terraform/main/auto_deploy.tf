#################################################
# IAM Roles and Policies for Lambda function
# for deploying SageMaker endpoint
#################################################

# define which services can asume this role
data "aws_iam_policy_document" "assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# define role
resource "aws_iam_role" "iam_for_lambda" {
  name               = "${var.account}-iam-for-lambda"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

# allows lambda to write CloudWatch Logs
resource "aws_iam_role_policy_attachment" "lambda_cloudwatch_access" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "lambda_s3_access" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

# allows lambda full SageMaker Access for Deploying the Endpoint
resource "aws_iam_role_policy_attachment" "lambda_sagermaker_full_access" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

#################################################
# Lambda function (from Docker image)
#################################################

resource "aws_lambda_function" "lambda_sagemaker_deploy" {
  function_name    = "deploy_sagemaker_endpoint"
  description      = "Deploys the latest and approved model"
  package_type     = "Image"
  role             = aws_iam_role.iam_for_lambda.arn
  image_uri        = "${var.operations_account}.dkr.ecr.${var.region}.amazonaws.com/lambda-image:latest"
  timeout          = 600                                                     # deployment can take 5 to 10min
  source_code_hash = filebase64sha256("./../../training_pipeline/deploy.py") # triggers update
}

#################################################
# EventBridge rule to invoke lambda function
#################################################

resource "aws_cloudwatch_event_rule" "lambda_invoke_rule" {
  name = "lambda-depolyment-invoker"
  event_pattern = jsonencode({
    "detail-type" : [
      "SageMaker Model Package State Change"
    ],
    "source" : [
      "aws.sagemaker"
    ],
  })
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule = aws_cloudwatch_event_rule.lambda_invoke_rule.name
  arn  = aws_lambda_function.lambda_sagemaker_deploy.arn
}

#################################################
# IAM role for EvenBridge to have permission to invoke Lambda function
#################################################

resource "aws_lambda_permission" "allow_cloudwatch_to_call_lambda" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_sagemaker_deploy.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.lambda_invoke_rule.arn
}
