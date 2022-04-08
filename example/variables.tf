variable "aws_region" {
  type    = string
  default = "eu-central-1"
}
variable "dns_zone" {
  type    = string
  default = "test.voximplant.com"
}
variable "dns_record" {
  type = string
  default = "2"
}
variable "dns_record_type" {
  type = string
  default = "A"
}
variable "dns_record_ttl" {
  type = number
  default = 300
}
variable "certbot_contact_email" {
  type    = string
  default = "usik@voximplant.com"
} 