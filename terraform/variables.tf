##############################################################################
# Input Variables
##############################################################################

variable "resource_group_name" {
  type        = string
  description = "Name of the resource group to create. Required if not using existing resource group"
  default     = null
}

variable "existing_resource_group_name" {
  type        = string
  description = "Name of the existing resource group.  Required if not creating new resource group"
  default     = null
}

variable "region" {
  type        = string
  description = "The region to be deployed in"
}

variable "secrets_manager_name" {
  type        = string
  description = "Name of Secrets-Manger instance to be created/retrieved according to create_secrets_manager true/false"
}

variable "sm_service_plan" {
  type        = string
  description = "Description of service plan to be used to provision Secrets Manager (only used if create_secrets_manager is true)"
  default     = "standard"
  validation {
    condition     = contains(["standard", "trial"], var.sm_service_plan)
    error_message = "The specified sm_service_plan is not a valid selection!"
  }
}

