#################################################
# IAM Roles and Policies for SageMaker
#################################################

# IAM role for SageMaker training job
data "aws_iam_policy_document" "sagemaker_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["sagemaker.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "sagemaker_exec_role" {
  name               = "${var.account}-sagemaker-exec"
  assume_role_policy = data.aws_iam_policy_document.sagemaker_assume_role.json
}

data "aws_iam_policy_document" "sagemaker_s3_policy" {
  statement {
    effect = "Allow"

    actions = [
      "s3:*"
    ]

    resources = [
      "*"
    ]
  }
}

# Policies for sagemaker execution training job
resource "aws_iam_policy" "sagemaker_s3_policy" {
  name   = "${var.account}-sagemaker-s3-policy"
  policy = data.aws_iam_policy_document.sagemaker_s3_policy.json
}

resource "aws_iam_role_policy_attachment" "s3_restricted_access" {
  role       = aws_iam_role.sagemaker_exec_role.name
  policy_arn = aws_iam_policy.sagemaker_s3_policy.arn
}

resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  role       = aws_iam_role.sagemaker_exec_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

#################################################
# Create SageMaker Domain and User-Profile
#################################################

resource "aws_sagemaker_domain" "sagemaker_domain" {
  domain_name = "training-domain"
  auth_mode   = "IAM"
  vpc_id      = module.vpc-network.network_id
  subnet_ids  = [module.vpc-network.public_subnetwork_id]

  default_user_settings {
    execution_role = aws_iam_role.sagemaker_exec_role.arn
  }
}

resource "aws_sagemaker_user_profile" "example" {
  domain_id         = aws_sagemaker_domain.sagemaker_domain.id
  user_profile_name = "training-domain-sagemaker-profile"
}
