#
# Cloud Resources
#
variable "name_prefix" {
  description = "A prefix used for naming resources"
  default     = "certbot"
}

variable "name" {
  description = "A name for naming resources"
}

variable "hosted_zones_ids" {
  description = "The id of the hosted zone that will be modified to prove ownership of the domain"
}

variable "function_trigger_schedule_expression" {
  description = "A cron-like expression that determines when the function is triggered"
  default     = "cron(0 */12 * * ? *)"
}

variable "tags" {
  description = "Resource Tags"
  default     = {}
}

variable "certificate_arn" {
  description = "Certificate ARN to update to"
}

#
# LetsEncrypt Certificate Settings
#
variable "contact_email" {
  description = "Contact email for LetsEncrypt notifications"
}

variable "certificate_domains" {
  description = "Comma separated domains list that will be included in the certificate"
}