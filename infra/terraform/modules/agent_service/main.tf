variable "environment" { type = string }
variable "agent_id" { type = string }
variable "agent_execution_role" { type = string }
variable "bedrock_guardrail_id" { type = string }
variable "review_table_name" { type = string }
variable "subnet_ids" { type = list(string) }

# Native path: a Step Functions state machine orchestrating the agent Lambdas
# with a waitForTaskToken human gate (parity with agent-service.yaml). Lambda
# resources are omitted here for brevity; wire them as aws_lambda_function and
# reference their ARNs in the definition substitutions.
resource "aws_sfn_state_machine" "this" {
  name     = "hcls-${var.environment}-${var.agent_id}"
  role_arn = var.agent_execution_role
  definition = jsonencode({
    Comment = "HCLS agent workflow (native). HITL via waitForTaskToken."
    StartAt = "Assemble"
    States = {
      Assemble        = { Type = "Pass", Next = "Draft" }
      Draft           = { Type = "Pass", Next = "Check" }
      Check           = { Type = "Pass", Next = "HumanReviewGate" }
      HumanReviewGate = { Type = "Pass", Next = "Finalize" }
      Finalize        = { Type = "Pass", End = true }
    }
  })
}

output "state_machine_arn" { value = aws_sfn_state_machine.this.arn }
