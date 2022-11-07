locals {
  tags = merge(var.tags, tomap({
    "Application" = "certbot-lambda"
  }))

  lambda_function_name = "${var.name_prefix}_${data.aws_region.current.name}_${var.name}"
}