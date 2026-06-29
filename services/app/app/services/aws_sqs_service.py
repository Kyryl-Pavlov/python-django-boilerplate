import json
import os

import boto3


def make_sqs_client():
    return boto3.client(
        "sqs",
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        endpoint_url=os.getenv("AWS_SQS_ENDPOINT_URL"),
    )


def ensure_queue(sqs, queue_url: str) -> None:
    queue_name = queue_url.rstrip("/").split("/")[-1]
    try:
        sqs.get_queue_url(QueueName=queue_name)
    except sqs.exceptions.QueueDoesNotExist:
        sqs.create_queue(QueueName=queue_name)


def send_event(event_type: str, payload: dict) -> str:
    """Publish an event to the SQS queue. Returns the SQS MessageId."""
    queue_url = os.environ["SQS_QUEUE_URL"]
    sqs = make_sqs_client()
    if os.getenv("AWS_SQS_ENDPOINT_URL"):
        # LocalStack only — queue is pre-created by Terraform in production
        ensure_queue(sqs, queue_url)
    body = json.dumps({"type": event_type, "payload": payload})
    response = sqs.send_message(QueueUrl=queue_url, MessageBody=body)
    return response["MessageId"]
