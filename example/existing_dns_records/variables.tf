variable "aws_region" {
  type    = string
  default = "eu-central-1"
}

variable "certificate_domains" {
  type = list
  default = [
    "8.test.voximplant.com",
    "9.test.voximplant.com"
  ]
}

variable "certbot_contact_email" {
  type    = string
  default = "usik@voximplant.com"
}