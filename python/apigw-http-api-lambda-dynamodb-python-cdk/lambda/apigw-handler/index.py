# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import os
import json
import uuid
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
from aws_lambda_powertools import Logger

# Patch all supported libraries for X-Ray tracing
patch_all()

logger = Logger(service="apigw-handler")

dynamodb_client = boto3.client("dynamodb")


def handler(event, context):
    # Extract correlation ID from request context
    correlation_id = event.get("requestContext", {}).get("requestId", str(uuid.uuid4()))
    logger.append_keys(correlation_id=correlation_id)
    
    table = os.environ.get("TABLE_NAME")
    logger.info("Processing request", extra={
        "table_name": table,
        "http_method": event.get("httpMethod"),
        "source_ip": event.get("requestContext", {}).get("identity", {}).get("sourceIp")
    })
    
    try:
        if event.get("body"):
            item = json.loads(event["body"])
            logger.info("Received payload", extra={"item": item})
            year = str(item["year"])
            title = str(item["title"])
            id = str(item["id"])
            dynamodb_client.put_item(
                TableName=table,
                Item={"year": {"N": year}, "title": {"S": title}, "id": {"S": id}},
            )
            message = "Successfully inserted data!"
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": message}),
            }
        else:
            logger.info("Received request without payload, using default data")
            dynamodb_client.put_item(
                TableName=table,
                Item={
                    "year": {"N": "2012"},
                    "title": {"S": "The Amazing Spider-Man 2"},
                    "id": {"S": str(uuid.uuid4())},
                },
            )
            message = "Successfully inserted data!"
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": message}),
            }
    except Exception as e:
        logger.exception("Error processing request", extra={
            "error_type": type(e).__name__,
            "error_message": str(e)
        })
        raise
