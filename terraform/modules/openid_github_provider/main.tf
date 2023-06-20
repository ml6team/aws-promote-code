#################################################
# OpenID provider for GitHub and IAM role with Full Access
#################################################

resource "aws_iam_openid_connect_provider" "github_openid_provider" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com",
  ]

  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]
}

resource "aws_iam_role" "github_access_role" {
  name               = "${var.account}-github-full-access"
  assume_role_policy = data.aws_iam_policy_document.assume_policy.json
}

data "aws_iam_policy_document" "assume_policy" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    effect = "Allow"

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github_openid_provider.arn]
    }
    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:ml6team/aws-promote-code:*"]
    }
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

  }
}

resource "aws_iam_role_policy_attachment" "github_full_access" {
  role       = aws_iam_role.github_access_role.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}
