variable "environment" { type = string }

resource "aws_kms_key" "this" {
  description         = "HCLS ${var.environment} per-customer key"
  enable_key_rotation = true
}

resource "aws_bedrock_guardrail" "this" {
  name                      = "hcls-${var.environment}-guardrail"
  blocked_input_messaging   = "Blocked by HCLS safety policy."
  blocked_outputs_messaging = "Withheld by HCLS safety policy."
  sensitive_information_policy_config {
    pii_entities_config { type = "US_SOCIAL_SECURITY_NUMBER" action = "BLOCK" }
    pii_entities_config { type = "EMAIL" action = "ANONYMIZE" }
  }
}

resource "aws_iam_role" "agent_exec" {
  name = "hcls-${var.environment}-agent-exec"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = ["ecs-tasks.amazonaws.com", "lambda.amazonaws.com", "bedrock.amazonaws.com"] },
      Action    = "sts:AssumeRole"
    }]
  })
}

output "kms_key_arn" { value = aws_kms_key.this.arn }
output "guardrail_id" { value = aws_bedrock_guardrail.this.guardrail_id }
output "agent_execution_role_arn" { value = aws_iam_role.agent_exec.arn }
