provider "aws" {
  shared_credentials_file = var.shared_credentials_file
  region                  = var.region
  profile              = var.profile
}

locals {
    sqs_queue_name = "SQS-${var.project}-${var.environment}-isl-fwd-${var.venue}-${var.sqs_queue_id}"
}


resource "aws_sqs_queue" "maap-hec-queue" {
  name = local.sqs_queue_name
}

data "aws_iam_policy_document" "maap-hec-queue" {
  policy_id = "SQSDefaultPolicy"
  statement {
    actions = [
      "SQS:SendMessage"
    ]
    effect = "Allow"
    principals {
      type        = "AWS"
      identifiers = ["*"]
    }
    sid = "Sid1571258347580"
  }
}

resource "aws_sqs_queue_policy" "maap-hec-queue" {
  depends_on = [aws_sqs_queue.maap-hec-queue, data.aws_iam_policy_document.maap-hec-queue]

  queue_url = aws_sqs_queue.maap-hec-queue.url
  policy = data.aws_iam_policy_document.maap-hec-queue.json
}


