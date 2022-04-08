locals {
  tags = merge(var.tags, tomap({
    "Application" = "certbot-lambda"
  }))
}