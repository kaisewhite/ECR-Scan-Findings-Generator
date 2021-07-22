#!/usr/bin/env python3
import os

# For consistency with TypeScript code, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.
from aws_cdk import core
from aws_cdk import core as cdk

from ecr_image_scan_findings.ecr_image_scan_findings import ECRImageScanFindingsStack

account_name_to_account_info = {
    "Sandbox": {"AccountId": "<AWS_ACCOUNT_NUMBER>", "env": "sandbox"},
    "NonProduction": {"AccountId": "<AWS_ACCOUNT_NUMBER>", "env": "nonprod"},
    "PreProduction": {"AccountId": "<AWS_ACCOUNT_NUMBER>", "env": "preprod"},
    "Production": {"AccountId": "<AWS_ACCOUNT_NUMBER>", "env": "prod"},
    "Mgmt": {"AccountId": "<AWS_ACCOUNT_NUMBER>", "env": "mgmt"},
    "Data": {"AccountId": "<AWS_ACCOUNT_NUMBER>", "env": "data"},
    "DevBi": {"AccountId": "<AWS_ACCOUNT_NUMBER>", "env": "devbi"},
    "PreProdBi": {"AccountId": "<AWS_ACCOUNT_NUMBER>", "env": "preprodbi"},
}
app = core.App()

account_ids_list = []
for account_name, account_info in account_name_to_account_info.items():
    print(f"{account_name}ECRImageScanFindingsStack")
    account_ids_list.append(account_info["AccountId"])

for account_name, account_info in account_name_to_account_info.items():
    ecr_resports_s3_bucket_name = "mgmt-ecr-scan-findings"

    if account_name == "Mgmt":
        ECRImageScanFindingsStack(
            app,
            f"{account_name.replace('_', '')}ECRImageScanFindingsStack",
            env_name=account_info["env"],
            account_ids_list=account_ids_list,
            s3_report_collection_bucket_name=ecr_resports_s3_bucket_name,
            create_s3_report_collection_bucket=True,
            env={
                "account": account_info["AccountId"],
                "region": "us-east-1",
            },
        )
    else:
        ECRImageScanFindingsStack(
            app,
            f"{account_name.replace('_','')}ECRImageScanFindingsStack",
            env_name=account_info["env"],
            s3_report_collection_bucket_name=ecr_resports_s3_bucket_name,
            create_s3_report_collection_bucket=False,
            env={
                "account": account_info["AccountId"],
                "region": "us-east-1",
            },
        )
# ECRImageScanFindingsStack(app, "ECRImageScanFindingsStack")

app.synth()
