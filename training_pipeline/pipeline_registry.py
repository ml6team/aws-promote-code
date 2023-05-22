"""Implements Pipeline Registry on top of AWS S3-bucket (in 'operations' account)"""
import json
import argparse

import boto3

import training_pipeline as tp
from aws_profiles import UserProfiles


class PipelineRegistry:
    def __init__(self, registry_profile: str) -> None:
        profile_id = UserProfiles().get_profile_id(registry_profile)
        self.bucket_name = f"{profile_id}-pipeline-registry-bucket"

    def get_file_path(self, pipeline_name: str, version_name: str) -> None:
        """Return file path, with specific folder for each pipeline"""
        return f"{pipeline_name}/pipeline_definition_{version_name}.json"

    def register_version(
        self,
        pipeline_name: str,
        json_data: dict,
        version_name: str,
        profile: str = None,
    ) -> None:
        """Register a new Pipeline JSON definition to the registry"""
        file_name = self.get_file_path(pipeline_name, version_name)

        session = boto3.Session(profile_name=profile) if profile else boto3.Session()

        s3 = session.resource("s3")
        s3object = s3.Object(self.bucket_name, file_name)

        s3object.put(Body=(bytes(json.dumps(json_data).encode("UTF-8"))))
        print(f"Saved file '{file_name}' in bucket '{self.bucket_name}'")

    def deploy_pipeline(
        self, pipeline_name: str, version_name: str, profile: str = None
    ) -> None:
        """Deploys a SageMaker pipeline by creating or updating
        an existing pipeline with the specified name."""

        session = boto3.Session(profile_name=profile) if profile else boto3.Session()

        sagemaker_client = session.client("sagemaker")
        iam = session.client("iam")
        profile_id = boto3.client("sts").get_caller_identity().get("Account")
        sagemaker_role = iam.get_role(RoleName=f"{profile_id}-sagemaker-exec")["Role"][
            "Arn"
        ]

        all_pipelines = [
            pipeline["PipelineName"]
            for pipeline in sagemaker_client.list_pipelines()["PipelineSummaries"]
        ]

        if pipeline_name in all_pipelines:
            sagemaker_client.delete_pipeline(PipelineName=pipeline_name)

        response = sagemaker_client.create_pipeline(
            PipelineName=pipeline_name,
            RoleArn=sagemaker_role,
            PipelineDefinitionS3Location={
                "Bucket": self.bucket_name,
                "ObjectKey": self.get_file_path(pipeline_name, version_name),
            },
        )
        print(response)


if __name__ == "__main__":
    userProfiles = UserProfiles()
    profiles = userProfiles.list_profiles()

    parser = argparse.ArgumentParser()
    parser.add_argument("--action", type=str, choices=["register", "deploy", "start"])
    parser.add_argument("--profile", default=None, type=str, choices=profiles)
    parser.add_argument(
        "--registry-profile", type=str, default="operations", choices=profiles
    )
    parser.add_argument("--region", type=str, default="eu-west-3")
    parser.add_argument("--pipeline-name", type=str, default="training-pipeline")
    parser.add_argument(
        "--git-commit-hash",
        type=str,
        default="ffac537e6cbbf934b08745a378932722df287a53",
    )  # dummy hash for now

    args = parser.parse_args()

    pipeline_registry = PipelineRegistry(registry_profile=args.registry_profile)

    if args.action == "register":
        pipeline = tp.get_pipeline(
            pipeline_name=args.pipeline_name,
            profile_name=args.profile,
            region=args.region,
        )
        pipeline_definition_json = json.loads(pipeline.definition())
        pipeline_registry.register_version(
            pipeline_name=args.pipeline_name,
            json_data=pipeline_definition_json,
            version_name=args.git_commit_hash,
            profile=args.profile,
        )

    elif args.action == "deploy":
        pipeline_registry.deploy_pipeline(
            profile=args.profile,
            pipeline_name=args.pipeline_name,
            version_name=args.git_commit_hash,
        )
    elif args.action == "start":
        tp.start_pipeline(
            profile_name=args.profile,
            pipeline_name=args.pipeline_name,
        )
