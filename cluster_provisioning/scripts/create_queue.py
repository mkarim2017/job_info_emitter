import boto3
import configparser
import os

CONFIG_FILER_PATH = r'maap-hec-config.py'

config = configparser.ConfigParser()
config.read(CONFIG_FILER_PATH)

print(config["AWS_SQS_QUEUE"])

os.environ["region_name"] = config["AWS_SQS_QUEUE"]["region_name"]
os.environ["AWS_ACCOUNT_ID"] = config["AWS_SQS_QUEUE"]["AWS_ACCOUNT_ID"]
os.environ["AWS_ACCESS_KEY"] = config["AWS_SQS_QUEUE"]["aws_access_key"]
os.environ["AWS_SECRET_ACCESS_KEY"] = config["AWS_SQS_QUEUE"]["aws_secret_key"]
os.environ["AWS_SESSION_TOKEN"] = config["AWS_SQS_QUEUE"]["aws_session_token"]

sqs_client = boto3.client('sqs', 
                      aws_access_key_id=os.environ["AWS_ACCESS_KEY"], 
                      aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"], 
                      region_name=os.environ["region_name"],
                      aws_session_token=os.environ["AWS_SESSION_TOKEN"]
                      )

queue = sqs_client.create_queue(QueueName=config["AWS_SQS_QUEUE"]["queue_name"])
queues = sqs_client.list_queues()
print(queues)
