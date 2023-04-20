#################################################
# IAM role for EvenBridge to trigger Sagemaker Pipeline
#################################################

# define which services can asume this role
data "aws_iam_policy_document" "eventbridge_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
  }
}

# define role
resource "aws_iam_role" "eventbridge_scheduler_exec_role" {
  name               = "${var.account}-eventbridge-scheduler-exec"
  assume_role_policy = data.aws_iam_policy_document.eventbridge_assume_role.json
}


// policy for sagemaker startpipeline
data "aws_iam_policy_document" "sagemaker_startpipeline_policy_doc" {
  statement {
    effect = "Allow"

    actions = [
      "sagemaker:StartPipelineExecution"
    ]

    resources = [
      "arn:aws:sagemaker:*:${var.account}:pipeline/*" # all pipelines in account
    ]
  }
}

# define policy
resource "aws_iam_policy" "sagemaker_startpipeline_policy" {
  name   = "${var.account}-sagemaker-startpipeline"
  policy = data.aws_iam_policy_document.sagemaker_startpipeline_policy_doc.json
}

# add policy to role
resource "aws_iam_role_policy_attachment" "eventbridge_startpipeline_access" {
  role       = aws_iam_role.eventbridge_scheduler_exec_role.name
  policy_arn = aws_iam_policy.sagemaker_startpipeline_policy.arn
}
