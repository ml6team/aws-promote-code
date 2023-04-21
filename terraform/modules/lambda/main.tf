resource "aws_iam_role" "iam_for_lambda" {
  name = "iam_lambda"
  assume_role_policy = jsonencode(
    {
      "Version" : "2012-10-17",
      "Statement" : [
        {
          "Action" : "sts:AssumeRole",
          "Principal" : {
            "Service" : "lambda.amazonaws.com"
          },
          "Effect" : "Allow",
          "Sid" : ""
        }
      ]
    }
  )
}

resource "aws_lambda_function" "lambda_function" {
  function_name = var.function_name
  package_type  = "Image"
  image_uri     = var.lambda_function_image_uri
  role          = aws_iam_role.iam_for_lambda.arn
  memory_size   = 10240
  timeout       = 30
}

# Infrastructure setup for S3 trigger
resource "aws_s3_bucket_notification" "incoming" {
  count  = var.trigger_bucket_name != "null" ? 1 : 0
  bucket = var.trigger_bucket_name

  lambda_function {
    lambda_function_arn = aws_lambda_function.lambda_function.arn
    events              = ["s3:ObjectCreated:*"]
    /******************************************
    Configure prefix or file extension when the lambda function should be triggered.
    filter_prefix       = "foldername"
    filter_suffix       = ".zip"
    *****************************************/
  }

  depends_on = [aws_lambda_permission.s3_permission_to_trigger_lambda]
}

resource "aws_lambda_permission" "s3_permission_to_trigger_lambda" {
  count         = var.trigger_bucket_name != "null" ? 1 : 0
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_function.arn
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::${var.trigger_bucket_name}"
}

# Infrastructure setup for SQS trigger
resource "aws_iam_role_policy_attachment" "lambda_function" {
  count      = var.trigger_queue_arn != "null" ? 1 : 0
  policy_arn = aws_iam_policy.lambda_function[0].arn
  role       = aws_iam_role.iam_for_lambda.name
}

resource "aws_iam_policy" "lambda_function" {
  count  = var.trigger_queue_arn != "null" ? 1 : 0
  policy = data.aws_iam_policy_document.lambda_function[0].json
}

data "aws_iam_policy_document" "lambda_function" {
  count = var.trigger_queue_arn != "null" ? 1 : 0
  statement {
    sid       = "AllowSQSPermissions"
    effect    = "Allow"
    resources = ["arn:aws:sqs:*"]

    actions = [
      "sqs:ChangeMessageVisibility",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes",
      "sqs:ReceiveMessage",
    ]
  }

  statement {
    sid       = "AllowInvokingLambdas"
    effect    = "Allow"
    resources = ["arn:aws:lambda:ap-southeast-1:*:function:*"]
    actions   = ["lambda:InvokeFunction"]
  }

  statement {
    sid       = "AllowCreatingLogGroups"
    effect    = "Allow"
    resources = ["arn:aws:logs:ap-southeast-1:*:*"]
    actions   = ["logs:CreateLogGroup"]
  }
  statement {
    sid       = "AllowWritingLogs"
    effect    = "Allow"
    resources = ["arn:aws:logs:ap-southeast-1:*:log-group:/aws/lambda/*:*"]

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
  }
}

resource "aws_lambda_event_source_mapping" "event_source_mapping" {
  count            = var.trigger_queue_arn != "null" ? 1 : 0
  event_source_arn = var.trigger_queue_arn
  enabled          = true
  function_name    = aws_lambda_function.lambda_function.arn
  batch_size       = 1
}


# Infrastructure setup for HTTP trigger
resource "aws_api_gateway_rest_api" "lambda_gateway" {
  count       = var.http_trigger ? 1 : 0
  name        = "ServerlessExample"
  description = "API Gateway to access serverless lambda function"
}

resource "aws_api_gateway_resource" "proxy" {
  count       = var.http_trigger ? 1 : 0
  rest_api_id = aws_api_gateway_rest_api.lambda_gateway[0].id
  parent_id   = aws_api_gateway_rest_api.lambda_gateway[0].root_resource_id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "proxy" {
  count         = var.http_trigger ? 1 : 0
  rest_api_id   = aws_api_gateway_rest_api.lambda_gateway[0].id
  resource_id   = aws_api_gateway_resource.proxy[0].id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "proxy_root" {
  count         = var.http_trigger ? 1 : 0
  rest_api_id   = aws_api_gateway_rest_api.lambda_gateway[0].id
  resource_id   = aws_api_gateway_rest_api.lambda_gateway[0].root_resource_id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda_root" {
  count       = var.http_trigger ? 1 : 0
  rest_api_id = aws_api_gateway_rest_api.lambda_gateway[0].id
  resource_id = aws_api_gateway_method.proxy_root[0].resource_id
  http_method = aws_api_gateway_method.proxy_root[0].http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.lambda_function.invoke_arn
}

resource "aws_api_gateway_integration" "lambda" {
  count       = var.http_trigger ? 1 : 0
  rest_api_id = aws_api_gateway_rest_api.lambda_gateway[0].id
  resource_id = aws_api_gateway_method.proxy[0].resource_id
  http_method = aws_api_gateway_method.proxy[0].http_method

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.lambda_function.invoke_arn
}

resource "aws_api_gateway_deployment" "lambda_function" {
  count = var.http_trigger ? 1 : 0
  depends_on = [
    aws_api_gateway_integration.lambda,
    aws_api_gateway_integration.lambda_root,
  ]

  rest_api_id = aws_api_gateway_rest_api.lambda_gateway[0].id
  stage_name  = "test"
}


resource "aws_lambda_permission" "apigw" {
  count         = var.http_trigger ? 1 : 0
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.lambda_function.function_name
  principal     = "apigateway.amazonaws.com"

  # The /*/* portion grants access from any method on any resource
  # within the API Gateway "REST API".
  source_arn = "${aws_api_gateway_rest_api.lambda_gateway[0].execution_arn}/*/*"
}

output "base_url" {
  value = aws_api_gateway_deployment.lambda_function[0].invoke_url
}



