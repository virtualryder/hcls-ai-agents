variable "environment" { type = string }
variable "kms_key_arn" { type = string }

resource "aws_dynamodb_table" "audit" {
  name         = "hcls-${var.environment}-audit"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "audit_id"
  range_key    = "ts"
  attribute { name = "audit_id" type = "S" }
  attribute { name = "ts" type = "S" }
  server_side_encryption { enabled = true kms_key_arn = var.kms_key_arn }
  point_in_time_recovery { enabled = true }
  lifecycle { prevent_destroy = true }
}

resource "aws_dynamodb_table" "review" {
  name         = "hcls-${var.environment}-review"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "request_id"
  attribute { name = "request_id" type = "S" }
}

output "audit_table_name" { value = aws_dynamodb_table.audit.name }
output "review_table_name" { value = aws_dynamodb_table.review.name }
