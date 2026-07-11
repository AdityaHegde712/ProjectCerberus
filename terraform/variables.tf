variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "ProjectCerberus"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "dashboard_origin" {
  description = "Dashboard origin for CORS configuration"
  type        = string
  default     = "https://dashboard.example.com"
}