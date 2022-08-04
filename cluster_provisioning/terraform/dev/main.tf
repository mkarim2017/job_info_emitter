provider "aws" {
  shared_credentials_file  = var.shared_credentials_file
  region                   = var.region
  profile                  = var.profile
}

module "common" {
  source = "../modules/common"

  sqs_queue_id             = var.sqs_queue_id
  shared_credentials_file  = var.shared_credentials_file
  profile                  = var.profile
  region                   = var.region
  project                  = var.project
  environment              = var.environment
  venue                    = var.venue
}
