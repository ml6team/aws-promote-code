"""Script to approve a model"""
import os
import sys
import logging
import argparse
import pandas as pd

import boto3

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

# def get_latest_approved_model_arn(model_package_group_name, sm_client):
#     """Retrieves the latest approved model from a given SageMaker model package group."""
#     # sm_client = boto3.client('sagemaker')
#     df = pd.DataFrame(sm_client.list_model_packages(
#         ModelPackageGroupName=model_package_group_name)["ModelPackageSummaryList"])
#     return df.iloc[0].ModelPackageArn


def approve_model():
    logger.info("Approve model")
    sm_client = boto3.Session(region_name="eu-west-3").client('sagemaker')
    model_package_group_arn = os.environ.get('model_package_group_arn')
    model_package_version = os.environ.get('model_package_version')
    
    logger.info(f"model_package_group_arn: {model_package_group_arn}")
    logger.info(f"model_package_version: {model_package_version}")
    
    
    # model_package_arn = get_latest_approved_model_arn(arn, sm_client)
    model_package_arn = model_package_group_arn + "/" + model_package_version
    
    logger.info(f"model_package_arn: {model_package_arn}")

    # update model status to 'approved'
    model_package_update_input_dict = {
        "ModelPackageArn": model_package_arn,
        "ModelApprovalStatus": "Approved"
    }
    _ = sm_client.update_model_package(**model_package_update_input_dict)


if __name__ == "__main__":
    approve_model()
