import logging

import boto3
import sagemaker


def deploy_model():
    logging.warning("Deploying model")
    sagemaker_session = sagemaker.session.Session()
    
    model_package_arn = f"arn:aws:sagemaker:{args.region}:{args.account}:" \
                        f"model-package/{args.model_package_name}/{str(args.model_version)}"

    # update model status to 'approved'
    model_package_update_input_dict = {
        "ModelPackageArn": model_package_arn,
        "ModelApprovalStatus": "Approved"
    }
    sm_client = boto3.Session().client('sagemaker')
    _ = sm_client.update_model_package(**model_package_update_input_dict)


if __name__ == "__main__":
    deploy_model()
