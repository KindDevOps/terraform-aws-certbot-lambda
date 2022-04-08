terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
    }
  }
}

provider "aws" {
  region = "${var.aws_region}"
}

module "certbot-lambda" {
  source  = "github.com/KindDevOps/terraform-aws-certbot-lambda?ref=master"

  name                                  = "test"
  contact_email                         = "${var.certbot_contact_email}"
  certificate_domains                   = "${var.dns_record}.${data.aws_route53_zone.test.name}"
  hosted_zone_id                        = data.aws_route53_zone.test.zone_id

  function_trigger_schedule_expression  = "cron(12 20 * * ? *)"
}

data "aws_route53_zone" "test" {
  name = "${var.dns_zone}"
  private_zone = false
}

resource "aws_route53_record" "test" {
  zone_id = data.aws_route53_zone.test.zone_id
  name    = "${var.dns_record}.${data.aws_route53_zone.test.name}"
  type    = var.dns_record_type
  ttl     = var.dns_record_ttl
  records = ["1.2.3.4"]
}