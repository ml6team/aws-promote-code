"""Deploy model from ModelRegistry ModelPackage"""
import argparse
import json
from datetime import datetime

from sagemaker import ModelPackage
import boto3
import botocore.exceptions
from boto3.session import Session
import sagemaker.session

from sagemaker.model_monitor import DataCaptureConfig


def get_latest_model(
    model_package_group_name: str, session: Session, is_approved=False
) -> str:
    """Retrieves the latest (optionally approved)
    model from a given SageMaker model package group."""
    sm_client = session.client("sagemaker")
    model_package_arns = sm_client.list_model_packages(
        ModelPackageGroupName=model_package_group_name
    )["ModelPackageSummaryList"]

    if is_approved:
        model_package_arns = [
            d for d in model_package_arns if d["ModelApprovalStatus"] == "Approved"
        ]

    if len(model_package_arns) != 0:
        model_package_arn = model_package_arns[0]["ModelPackageArn"]
        print(f"The latest approved model-arn is: {model_package_arn}")
        return model_package_arn

    else:
        print(
            f"There is no approved model in the model-group '{model_package_group_name}'"
        )


def deploy(
    role_arn: str, model_package_arn: str, account: str, session: Session
) -> None:
    """Deploys or updates model endpoint"""
    # print(f"Deploy model: {model_package_arn}")
    endpoint_name = f"{account}-endpoint"

    sagemaker_session = sagemaker.session.Session(boto_session=session)
    model = ModelPackage(
        role=role_arn,
        model_package_arn=model_package_arn,
        sagemaker_session=sagemaker_session,
    )
    instance_type = "ml.g4dn.xlarge"

    try:
        print("Start model deployment")
        model.deploy(
            initial_instance_count=1,
            instance_type=instance_type,
            data_capture_config=DataCaptureConfig(
                enable_capture=True,
            ),
            endpoint_name=endpoint_name,
        )
        print(f"Deployed new model endpoint: '{endpoint_name}'")
    except botocore.exceptions.ClientError:
        print("Start model update")
        sm_session = model.sagemaker_session
        model.create()

        # Create endpoint config
        endpoint_config_name = sm_session.create_endpoint_config(
            initial_instance_count=1,
            instance_type=instance_type,
            name=datetime.now().strftime("%Y-%m-%d-%H-%M-%S"),
            model_name=model.name,
        )

        # Update desired endpoint with new Endpoint Config
        client = session.client("sagemaker")
        client.update_endpoint(
            EndpointName=endpoint_name, EndpointConfigName=endpoint_config_name
        )
        print(f"Updated model endpoint: '{endpoint_name}'")


def lambda_func(event, context):
    """Is run from AWS Lambda function image (see /images/lambda/Dockerfile).
    Checks if status-change was from latest model and if this model is "approved",
    before deploying endpoint
    """
    # extract relevant info from event-json
    account = event["account"]
    region = event["region"]
    model_package_name = event["detail"]["ModelPackageGroupName"]
    model_version = event["detail"]["ModelPackageVersion"]
    status = event["detail"]["ModelApprovalStatus"]

    model_package_arn = (
        f"arn:aws:sagemaker:{region}:{account}:"
        f"model-package/{model_package_name}/{str(model_version)}"
    )
    session = boto3.Session()
    if (
        model_package_arn.lower()
        != get_latest_model(model_package_name, session).lower()
    ):
        print(
            f"Lambda triggered by model: '{model_package_arn}', which is not the latest model"
        )
        return {"statusCode": 200, "body": json.dumps("Model NOT deployed")}

    if status != "Approved":
        print(
            f"Lambda triggered by model: '{model_package_arn}', but model was not approved"
        )
        return {"statusCode": 200, "body": json.dumps("Model NOT deployed")}

    role_arn = f"arn:aws:iam::{account}:role/{account}-iam-for-lambda"
    deploy(
        role_arn=role_arn,
        model_package_arn=model_package_arn,
        account=account,
        session=session,
    )

    return {"statusCode": 200, "body": json.dumps("Model deployed")}


if __name__ == "__main__":
    # only import when executed directly (not inside lambda func)
    from aws_profiles import UserProfiles

    userProfiles = UserProfiles()
    profiles = userProfiles.list_profiles()

    parser = argparse.ArgumentParser()

    parser.add_argument("--profile", type=str, default=None, choices=profiles)
    parser.add_argument("--region", type=str, default="eu-west-3")
    parser.add_argument(
        "--model-package-name", type=str, default="training-pipelineModelGroup"
    )
    parser.add_argument("--model-version", type=int, default=None)
    args = parser.parse_args()

    session = (
        boto3.Session(profile_name=args.profile) if args.profile else boto3.Session()
    )
    account_id = session.client("sts").get_caller_identity().get("Account")

    iam = session.client("iam")
    role_arn = iam.get_role(RoleName=f"{account_id}-sagemaker-exec")["Role"]["Arn"]

    if args.model_version is not None:
        model_package_arn = (
            f"arn:aws:sagemaker:{args.region}:{account_id}:"
            f"model-package/{args.model_package_name}/{str(args.model_version)}"
        )
    else:
        model_package_arn = get_latest_model(
            args.model_package_name, session, is_approved=True
        )

    deploy(
        role_arn=role_arn,
        model_package_arn=model_package_arn,
        account=account_id,
        session=session,
    )
