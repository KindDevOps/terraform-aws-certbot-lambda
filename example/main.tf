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
  source  = "github.com/KindDevOps/terraform-aws-certbot-lambda?ref=acm_certs"

  name                                  = "${local.record}-${local.zone_name}"
  contact_email                         = "${var.certbot_contact_email}"
  certificate_domains                   = "${var.dns_record}.${data.aws_route53_zone.zone.name}"
  hosted_zone_id                        = data.aws_route53_zone.zone.zone_id
  certificate_arn                       = "${var.certificate_arn}"
  
  function_trigger_schedule_expression  = "cron(12 20 * * ? *)"
}

locals {
  zone_name = replace(regex("(.*)([[:punct:]]$)", "${data.aws_route53_zone.zone.name}")[0], ".", "-")
  record = replace("${var.dns_record}", ".", "-")
}

data "aws_route53_zone" "zone" {
  name = "${var.dns_zone}"
  private_zone = false
}

resource "aws_route53_record" "dns_record" {
  zone_id = data.aws_route53_zone.zone.zone_id
  name    = "${var.dns_record}.${data.aws_route53_zone.zone.name}"
  type    = var.dns_record_type
  ttl     = var.dns_record_ttl
  records = ["1.2.3.4"]
}