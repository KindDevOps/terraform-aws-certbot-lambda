#
# Lambda function that takes care of requesting the creation and renewal of
# LetsEncrypt certificates and stores them in an S3 bucket.
#
module "certbot_lambda" {
  # source = "github.com/KindDevOps/terraform-aws-lambda?ref=v1.48.0"
  source = "github.com/KindDevOps/terraform-aws-lambda?ref=v3.1.0"

  function_name = local.lambda_function_name
  description   = "CertBot Lambda that creates and renews certificates for ${var.certificate_domains}"
  handler       = "main.lambda_handler"
  runtime       = "python3.9"
  timeout       = 300

  source_path = "${path.module}/src/"

  trusted_entities = ["events.amazonaws.com"]
  
  attach_policy_json = true
  policy_json = data.aws_iam_policy_document.lambda_permissions.json

  environment_variables = {
      EMAIL     = var.contact_email
      DOMAINS   = var.certificate_domains
      CERT_ARN  = var.certificate_arn
  }
}

data "aws_region" "current" {}

#
# Lambda permissions.
#
data "aws_iam_policy_document" "lambda_permissions" {
  statement {
    actions = [
      "route53:ListHostedZones",
      "route53:GetChange"
    ]
    resources = ["*"]
  }

  statement {
    actions = [
      "route53:ChangeResourceRecordSets"
    ]
    resources = [
       for zone_id in var.hosted_zones_ids : format("arn:aws:route53:::hostedzone/%s", zone_id.zone_id)
    ]
  }

  statement {
    actions = [
      "acm:ImportCertificate",
      "acm:DescribeCertificate"
    ]
    resources = [
      var.certificate_arn
    ]
  }
}
