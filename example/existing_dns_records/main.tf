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
  source  = "github.com/KindDevOps/terraform-aws-certbot-lambda?ref=acm_only"

  name                                  = "${local.lambda-name}"
  contact_email                         = "${var.certbot_contact_email}"
  certificate_domains                   = "${local.certificate_domains}"
  # Route53 Zones list to apply policy
  hosted_zones_ids                      = data.aws_route53_zone.zones
  certificate_arn                       = aws_acm_certificate.cert.arn
  
  function_trigger_schedule_expression  = "cron(12 20 * * ? *)"
}

locals {
  #zone_name = replace(regex("(.*)([[:punct:]]$)", "${data.aws_route53_zone.zone.name}")[0], ".", "-")
  lambda-name = replace("${var.certificate_domains[0]}", ".", "-")
  certificate_domains = join(",", var.certificate_domains )
}

data "aws_route53_zone" "zones" {
  for_each = toset( var.certificate_domains )

  name = regex(".*?[[:punct:]](.*)", each.value)[0] 
  private_zone = false
}

resource "tls_private_key" "stub" {
  algorithm = "RSA"
}

resource "tls_self_signed_cert" "stub" {
  private_key_pem = tls_private_key.stub.private_key_pem

  subject {
    common_name  = "${var.certificate_domains[0]}"
    organization = "ACME Examples, Inc"
  }

  validity_period_hours = 12

  allowed_uses = [
    "key_encipherment",
    "digital_signature",
    "server_auth",
  ]
}

resource "aws_acm_certificate" "cert" {
  private_key      = tls_private_key.stub.private_key_pem
  certificate_body = tls_self_signed_cert.stub.cert_pem
}