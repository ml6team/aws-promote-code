# #################################################
# # ECR for lambda image
# #################################################

resource "aws_ecr_repository" "lambda_ecr" {
  name = "lambda-image"
  image_scanning_configuration {
    scan_on_push = true
  }
  image_tag_mutability = "MUTABLE"
}

# give other accounts rights to download images
data "aws_iam_policy_document" "allow_access_to_lambda_ecr" {
  statement {
    sid    = "Allow lambda acces to ECR"
    effect = "Allow"
    principals {
      type = "AWS"
      identifiers = [
        "arn:aws:iam::${var.dev_account_id}:root",     # dev
        "arn:aws:iam::${var.staging_account_id}:root", # staging
        "arn:aws:iam::${var.prod_account_id}:root",    # prod
      ]
    }
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = [
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
    ]
    resources = [
    ]
  }
}

resource "aws_ecr_repository_policy" "lambda_add_ecr_policy" {
  repository = aws_ecr_repository.lambda_ecr.name
  policy     = data.aws_iam_policy_document.allow_access_to_lambda_ecr.json
}

# #################################################
# # ECR for training image
# #################################################

resource "aws_ecr_repository" "training_ecr" {
  name = "training-image"
}

# give other accounts rights to download images
data "aws_iam_policy_document" "allow_access_to_training_ecr" {
  statement {
    sid    = "Allow SageMaker acces to ECR"
    effect = "Allow"
    principals {
      type = "AWS"
      identifiers = [
        "arn:aws:iam::${var.dev_account_id}:root",     # dev
        "arn:aws:iam::${var.staging_account_id}:root", # staging
        "arn:aws:iam::${var.prod_account_id}:root",    # prod
      ]
    }
    principals {
      type        = "Service"
      identifiers = ["sagemaker.amazonaws.com"]
    }
    actions = [
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
    ]
    resources = [
    ]
  }
}

resource "aws_ecr_repository_policy" "training_add_ecr_policy" {
  repository = aws_ecr_repository.training_ecr.name
  policy     = data.aws_iam_policy_document.allow_access_to_training_ecr.json
}
