# ⚠️ REFERENCE SKELETON — NOT at parity with the CloudFormation golden paths.
# CloudFormation/SAM is the canonical, validated IaC. See docs/TERRAFORM-AND-GOVCLOUD-STATUS.md
# for the coverage matrix and gaps before relying on this.

variable "environment" { type = string }

resource "aws_vpc" "this" {
  cidr_block           = "10.40.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags                 = { Name = "hcls-${var.environment}-vpc" }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.this.id
  cidr_block        = cidrsubnet(aws_vpc.this.cidr_block, 8, count.index + 11)
  availability_zone = data.aws_availability_zones.available.names[count.index]
  tags              = { Name = "hcls-${var.environment}-private-${count.index}" }
}

data "aws_availability_zones" "available" { state = "available" }

output "vpc_id" { value = aws_vpc.this.id }
output "private_subnet_ids" { value = aws_subnet.private[*].id }
