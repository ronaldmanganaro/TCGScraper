variable "region" {
  description = "The AWS region to deploy resources in"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "The type of AWS instance to create"
  type        = string
  default     = "t2.micro"
}