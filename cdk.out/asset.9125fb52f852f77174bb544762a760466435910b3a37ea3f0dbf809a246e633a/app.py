import csv
import datetime
import json
import boto3
import logging
import io
import csv
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)
ecr = boto3.client('ecr')
sns = boto3.client('sns')
s3 = boto3.resource('s3')


def get_findings():
    bucket_prefix = os.environ.get('bucket_prefix', 'Not Set')
    stream = io.StringIO()
    headers = ['repositoryName', 'imageTags',
               'vulnerability', 'severity', 'description']
    writer = csv.DictWriter(stream, delimiter=',',
                            lineterminator='\n', fieldnames=headers)
    writer.writeheader()

    repositories = []
    repositories_resp = ecr.describe_repositories()
    repositories = repositories + repositories_resp["repositories"]

    while "NextToken" in repositories_resp:
        repositories_resp = ecr.describe_repositories(
            NextToken=repositories_resp["NextToken"])
        repositories = repositories + repositories_resp["repositories"]

    for repository in repositories:
        images = []
        images_resp = ecr.describe_images(
            repositoryName=repository["repositoryName"], registryId=repository["registryId"]
        )
        images = images + images_resp["imageDetails"]

        while "NextToken" in images_resp:
            images_resp = ecr.describe_images(
                repositoryName=repository["repositoryName"], registryId=repository["registryId"]
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
                findings = response['imageScanFindings']['findings']

                for finding in findings:
                    if finding['severity'] == "HIGH" or finding['severity'] == "CRITICAL":
                        writer.writerow({"repositoryName": response['repositoryName'], "imageTags": imageTags,
                                         "vulnerability": finding['name'], "severity": finding['severity'], "description": finding['description']})

    csv_string_object = stream.getvalue()
    s3.Object(f'{bucket_prefix}-ecr-image-scan-findings',
              f'{bucket_prefix}-ecr-image-scan-findings.csv').put(Body=csv_string_object)


def lambda_handler(event, context):
    scan_result = get_findings()
    logger.info(scan_result)
