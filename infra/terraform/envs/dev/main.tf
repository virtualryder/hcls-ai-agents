# HCLS Agent Suite — dev environment root module (parity with CloudFormation).
terraform {
  required_version = ">= 1.6"
  required_providers {
    aws = { source = "hashicorp/aws", version = ">= 5.40" }
  }
}

provider "aws" {
  region = var.region
}

variable "region" { default = "us-east-1" }
variable "environment" { default = "dev" }
variable "agent_id" { default = "01-regulatory-writing" }

module "network" {
  source      = "../../modules/network"
  environment = var.environment
}

module "security" {
  source      = "../../modules/security"
  environment = var.environment
}

module "data" {
  source      = "../../modules/data"
  environment = var.environment
  kms_key_arn = module.security.kms_key_arn
}

module "agent_service" {
  source                = "../../modules/agent_service"
  environment           = var.environment
  agent_id              = var.agent_id
  agent_execution_role  = module.security.agent_execution_role_arn
  bedrock_guardrail_id  = module.security.guardrail_id
  review_table_name     = module.data.review_table_name
  subnet_ids            = module.network.private_subnet_ids
}

output "guardrail_id" { value = module.security.guardrail_id }
output "audit_table" { value = module.data.audit_table_name }
