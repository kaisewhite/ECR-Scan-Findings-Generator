import os
from typing import Dict, List, Optional

from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda, aws_lambda_python
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_sns as sns
from aws_cdk import aws_sns_subscriptions as subscriptions
from aws_cdk import core
from aws_cdk import core as cdk

# For consistency with other languages, `cdk` is the preferred import name for
# the CDK's core module.  The following line also imports it as `core` for use
# with examples from the CDK Developer's Guide, which are in the process of
# being updated to use `cdk`.  You may delete this import if you don't need it.


class ECRImageScanFindingsStack(cdk.Stack):
    def __init__(
        self,
        scope: cdk.Construct,
        construct_id: str,
        env_name: str,
        account_ids_list: Optional[List[str]] = None,
        s3_report_collection_bucket_name: Optional[str] = None,
        create_s3_report_collection_bucket: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ecr_access_policy_statement = iam.PolicyStatement(
            actions=[
                "ec2:CreateNetworkInterface",
                "ec2:DescribeNetworkInterfaces",
                "ec2:DeleteNetworkInterface",
                "xray:*",
                "ecr:GetRegistryPolicy",
                "ecr:DescribeImageScanFindings",
                "ecr:GetLifecyclePolicyPreview",
                "ecr:GetDownloadUrlForLayer",
                "ecr:DescribeRegistry",
                "ecr:GetAuthorizationToken",
                "ecr:ListTagsForResource",
                "ecr:ListImages",
                "ecr:BatchGetImage",
                "ecr:DescribeImages",
                "ecr:DescribeRepositories",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetRepositoryPolicy",
                "ecr:GetLifecyclePolicy",
            ],
            resources=["*"],
        )

        s3_report_bucket_policy_statement = iam.PolicyStatement(
            actions=[
                "s3:Put*",
                "s3:Get*",
                "s3:List*",
            ],
            resources=[
                f"arn:aws:s3:::{s3_report_collection_bucket_name}/*",
                f"arn:aws:s3:::{s3_report_collection_bucket_name}",
            ],
        )

        lambda_layer = aws_lambda_python.PythonLayerVersion(
            self,
            "EndpointMonitoringLayer",
            entry="./ecr_image_scan_findings/lambda_layer/",
            compatible_runtimes=[
                aws_lambda.Runtime.PYTHON_3_7,
                aws_lambda.Runtime.PYTHON_3_8,
            ],
        )

        function = aws_lambda_python.PythonFunction(
            self,
            "ecr-image-scan-findings-generator",
            entry="./ecr_image_scan_findings/lambda/image_findings",
            index="app.py",
            handler="lambda_handler",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            timeout=cdk.Duration.minutes(3),
            function_name="ecr-image-scan-findings-generator",
            layers=[lambda_layer],
            environment={
                "ENV": env_name,
                "ECR_FINDINGS_BUCKET_NAME": s3_report_collection_bucket_name,
            },
        )

        function.add_to_role_policy(ecr_access_policy_statement)
        function.add_to_role_policy(s3_report_bucket_policy_statement)

        schedule = events.Rule(
            self,
            "EcrScanningReportSchedule",
            enabled=True,
            description="Schedule Regular ECR Scanning Report Collection",
            schedule=events.Schedule.expression(expression="cron(0 8 ? * MON-FRI *)"), #every 5 mins
            targets=[targets.LambdaFunction(function)],
        )

        # NOTE: Uncomment if you would like to use an existing buckets
        # bucket = s3.Bucket.from_bucket_attributes(self, "ImportedBucket",
        #                                          bucket_arn="arn:aws:s3:::mgmt-ecr-image-scan-findings"
        #                                          )

        if create_s3_report_collection_bucket:
            bucket = s3.Bucket(
                self,
                f"{env_name}-ecr-image-scan-findings-bucket",
                bucket_name=s3_report_collection_bucket_name,
                removal_policy=cdk.RemovalPolicy.DESTROY,
                block_public_access=s3.BlockPublicAccess.BLOCK_ALL,  # needed to for all s3 bucket
                auto_delete_objects=True,
                versioned=True,
            )
            for account_id in account_ids_list:
                bucket.grant_read_write(iam.AccountPrincipal(account_id))
            # bucket.grant_read_write(function)
