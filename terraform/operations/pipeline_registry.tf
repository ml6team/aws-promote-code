/******************************************
  S3 bucket for Pipeline Registry
 *****************************************/

resource "aws_s3_bucket" "pipeline_registry" {
  bucket = "${var.account}-pipeline-registry-bucket"
}

/******************************************
  Access to the Pipeline Registry from other accounts
 *****************************************/

resource "aws_s3_bucket_policy" "allow_access_from_another_account" {
  bucket = aws_s3_bucket.pipeline_registry.id
  policy = data.aws_iam_policy_document.allow_access_from_another_account.json
}

data "aws_iam_policy_document" "allow_access_from_another_account" {
  statement {

    # dev
    principals {
      type        = "AWS"
      identifiers = ["${var.dev_account_id}"]
    }

    # staging
    principals {
      type        = "AWS"
      identifiers = ["${var.staging_account_id}"]
    }

    # prod
    principals {
      type        = "AWS"
      identifiers = ["${var.prod_account_id}"]
    }

    actions = [
      # "s3:GetObject",
      # "s3:ListBucket",
      "*"
    ]

    resources = [
      aws_s3_bucket.pipeline_registry.arn,
      "${aws_s3_bucket.pipeline_registry.arn}/*",
    ]
  }
}
