from sagemaker import ModelPackage
import boto3
import sagemaker.session
import argparse


def deploy(role_arn: str, model_package_arn: str) -> None:
    sagemaker_session = sagemaker.session.Session()

    # update model status to 'approved'
    model_package_update_input_dict = {
        "ModelPackageArn": model_package_arn,
        "ModelApprovalStatus": "Approved"
    }
    sm_client = boto3.Session().client('sagemaker')
    _ = sm_client.update_model_package(
        **model_package_update_input_dict)

    # deploy model to endpoint
    model = ModelPackage(role=role_arn, model_package_arn=model_package_arn,
                         sagemaker_session=sagemaker_session)

    model.deploy(initial_instance_count=1, instance_type='ml.g4dn.xlarge')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--account', type=str, default="101436505502")
    parser.add_argument('--region', type=str, default="eu-west-3")
    parser.add_argument('--model-package-name', type=str,
                        default="training-pipelineModelGroup")
    parser.add_argument('--model-version', type=int, default=1)
    args = parser.parse_args()

    iam = boto3.client('iam')
    role_arn = iam.get_role(
        RoleName=f'{args.account}-sagemaker-exec')['Role']['Arn']

    model_package_arn = f"arn:aws:sagemaker:{args.region}:{args.account}:" \
                        f"model-package/{args.model_package_name}/{str(args.model_version)}"

    deploy(role_arn=role_arn, model_package_arn=model_package_arn)
