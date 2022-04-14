variable "aws_region" {
  type    = string
  default = "us-east-2"
}

variable "certificate_domains" {
  type = list
  default = [
    ".voximplant.com",
    "*.voximplant.com",
    ".voximplant.ru",
    "*.voximplant.ru"
  ]
  # Front dots should be used to allow automatic Route53 zone id detection for second level domains.
}

variable "certbot_contact_email" {
  type    = string
  default = "usik@voximplant.com"
}