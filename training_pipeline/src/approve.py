"""Script to approve a model (pipeline step)"""
import os
import sys
import logging

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


def approve_model():
    logger.info("Approve model")
    sm_client = boto3.Session(region_name="eu-west-3").client("sagemaker")
    model_package_group_arn = os.environ.get("model_package_group_arn")
    model_package_version = os.environ.get("model_package_version")

    logger.info(f"model_package_group_arn: {model_package_group_arn}")
    logger.info(f"model_package_version: {model_package_version}")

    model_package_arn = model_package_group_arn + "/" + model_package_version

    logger.info(f"model_package_arn: {model_package_arn}")

    # update model status to 'approved'
    model_package_update_input_dict = {
        "ModelPackageArn": model_package_arn,
        "ModelApprovalStatus": "Approved",
    }
    sm_client.update_model_package(**model_package_update_input_dict)


if __name__ == "__main__":
    approve_model()
