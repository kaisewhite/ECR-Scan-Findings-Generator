import csv
import datetime
import io
import json
import os

import boto3
from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
logger = Logger(service="ecr-vuln-scanner", level=LOG_LEVEL)
logger.setLevel(LOG_LEVEL)

ecr = boto3.client("ecr")
sns = boto3.client("sns")
s3 = boto3.resource("s3")

ENV = os.environ.get("ENV", "sandbox")
ECR_FINDINGS_BUCKET_NAME = os.environ.get("ECR_FINDINGS_BUCKET_NAME")


def get_findings():
    bucket_prefix = os.environ.get('bucket_prefix', 'Not Set')
    stream = io.StringIO()
    headers = [
        "repositoryName",
        "imageTags",
        "vulnerability",
        "severity",
        "description",
    ]
    writer = csv.DictWriter(
        stream, delimiter=",", lineterminator="\n", fieldnames=headers
    )
    writer.writeheader()

    repositories = []
    repositories_resp = ecr.describe_repositories()
    repositories = repositories + repositories_resp["repositories"]

    while "NextToken" in repositories_resp:
        repositories_resp = ecr.describe_repositories(
            NextToken=repositories_resp["NextToken"]
        )
        repositories = repositories + repositories_resp["repositories"]

    for repository in repositories:
        images = []
        images_resp = ecr.describe_images(
            repositoryName=repository["repositoryName"],
            registryId=repository["registryId"],
        )
        images = images + images_resp["imageDetails"]

        while "NextToken" in images_resp:
            images_resp = ecr.describe_images(
                repositoryName=repository["repositoryName"],
                registryId=repository["registryId"],
            )
            images = images + images_resp["imageDetails"]

        for image in images:
            imageTags = image.get("imageTags", [""])[0]
            imageScanStatus = image.get("imageScanStatus", {}).get("status")
            if imageScanStatus == "COMPLETE":
                response = ecr.describe_image_scan_findings(
                    registryId=image["registryId"],
                    repositoryName=image["repositoryName"],
                    imageId={"imageDigest": image["imageDigest"]},
                )
                findings = response["imageScanFindings"]["findings"]

                for finding in findings:
                    if (
                        finding["severity"] == "HIGH"
                        or finding["severity"] == "CRITICAL"
                    ):
                        writer.writerow(
                            {
                                "repositoryName": response["repositoryName"],
                                "imageTags": imageTags,
                                "vulnerability": finding["name"],
                                "severity": finding["severity"],
                                "description": finding["description"],
                            }
                        )

    csv_string_object = stream.getvalue()
    s3.Object(ECR_FINDINGS_BUCKET_NAME, f"{ENV}-ecr-image-scan-findings.csv").put(
        Body=csv_string_object, ACL="bucket-owner-full-control"
    )


def lambda_handler(event, context):
    scan_result = get_findings()
    logger.info(scan_result)
