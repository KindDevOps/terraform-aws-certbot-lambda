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
  default = "5"
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

variable "certificate_arn" {
  description = "Certificate ARN to update to"
  default     = "arn:aws:acm:eu-central-1:827460979007:certificate/38227fce-b5ca-4e2b-bbb9-7e19a7295ce1"
}