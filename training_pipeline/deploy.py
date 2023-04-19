"""Deploy model from ModelRegistry ModelPackage"""
import argparse
import pandas as pd

from sagemaker import ModelPackage
import boto3
import sagemaker.session

from sagemaker.model_monitor import DataCaptureConfig


def get_latest_approved_model(model_package_group_name):
    """Retrieves the latest approved model from a given SageMaker model package group."""
    sm_client = boto3.client('sagemaker')
    model_package_arns = sm_client.list_model_packages(
        ModelPackageGroupName=model_package_group_name)["ModelPackageSummaryList"]
    
    approved_model_package_arns = [d for d in model_package_arns if d['ModelApprovalStatus'] == "Approved"]
    
    if len(approved_model_package_arns) != 0:
        model_package_arn = approved_model_package_arns[0]["ModelPackageArn"]
        print(f"The latest approved model-arn is: {model_package_arn}")
        return model_package_arn

    else:
        print(f"There is no approved model in the model-group '{model_package_group_name}'")


def approve_model(model_package_arn):
    # update model status to 'approved'
    model_package_update_input_dict = {
        "ModelPackageArn": model_package_arn,
        "ModelApprovalStatus": "Approved"
    }
    sm_client = boto3.Session().client('sagemaker')
    sm_client.update_model_package(**model_package_update_input_dict)


def deploy(role_arn: str, model_package_arn: str) -> None:
    print(f"Deploy model: {model_package_arn}")
    sagemaker_session = sagemaker.session.Session()

    # deploy model to endpoint
    model = ModelPackage(role=role_arn, model_package_arn=model_package_arn,
                         sagemaker_session=sagemaker_session)

    data_capture_config = DataCaptureConfig(
        enable_capture=True,
        # sampling_percentage = sampling_percentage, # Optional
        # destination_s3_uri = s3_capture_upload_path, # Optional
    )

    model.deploy(
        initial_instance_count=1,
        instance_type='ml.g4dn.xlarge',
        data_capture_config=data_capture_config,
        # endpoint_name="",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--account', type=str, default="101436505502")
    parser.add_argument('--region', type=str, default="eu-west-3")
    parser.add_argument('--model-package-name', type=str,
                        default="training-pipelineModelGroup")
    parser.add_argument('--model-version', type=int)
    args = parser.parse_args()

    iam = boto3.client('iam')
    role_arn = iam.get_role(
        RoleName=f'{args.account}-sagemaker-exec')['Role']['Arn']

    if args.model_version is not None:
        model_package_arn = f"arn:aws:sagemaker:{args.region}:{args.account}:" \
                            f"model-package/{args.model_package_name}/{str(args.model_version)}"
    else:
        model_package_arn = get_latest_approved_model(args.model_package_name)
    
    deploy(role_arn=role_arn, model_package_arn=model_package_arn)
