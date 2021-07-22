# Welcome to your ECR Findings Scanner CDK Python project!

This project is setup to loop through ECR repositories in multiple AWS accounts and return a list of vulnerabilities from each scanned image [ecr.describe_image_scan_findings()](https://docs.aws.amazon.com/cli/latest/reference/ecr/describe-image-scan-findings.html)
It will create a centralized s3 bucket and stored the results in in a `.csv`. Note: It will only return results if the image has already been scanned.

Note: All AWS accounts have to be bootstrapped prior.

TODO:

- Add [start-image-scan](https://docs.aws.amazon.com/cli/latest/reference/ecr/start-image-scan.html) functionality in `ecr_image_scan_findings/lambda/image_findings/app.py`

## How to deploy this project from the terminal

- Within the root directory run `cdk synth --profile <AWS-PROFILE>`
- After a successful synth then run `cdk deploy --profile <AWS-PROFILE>`

## How to use SAM to run/debug the lambda function locally

- Navigate to `ecr_image_scan_findings/lambda`
- Run the following command: `sam build --use-container && sam local invoke --profile <AWS-PROFILE>`

## To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

- `cdk ls` list all stacks in the app
- `cdk synth` emits the synthesized CloudFormation template
- `cdk deploy` deploy this stack to your default AWS account/region
- `cdk diff` compare deployed stack with current state
- `cdk docs` open CDK documentation
- `python3 -m venv .venv` stary python virtual environment
- `sam build --use-container && sam local invoke --profile <AWS-PROFILE>` - Run lambda function locally

Enjoy!
