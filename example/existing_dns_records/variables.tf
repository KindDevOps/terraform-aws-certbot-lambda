variable "aws_region" {
  type    = string
  default = "eu-central-1"
}

variable "certificate_domains" {
  type = list
  default = [
    ".voximplant.com",
    "www.voximplant.com",
    ".voximplant.ru",
    "www.voximplant.ru"
  ]
  # Dots should be used to allow automatic Route53 zone detection for second level domains.
}

variable "certbot_contact_email" {
  type    = string
  default = "usik@voximplant.com"
}