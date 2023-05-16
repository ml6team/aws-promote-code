"""Implements Pipeline Registry on top of AWS S3-bucket (in 'operations' account)"""
import json
import argparse

import boto3

import training_pipeline as tp
from aws_profiles import UserProfiles


class PipelineRegistry:
    def __init__(self, registry_profile: str, userProfiles) -> None:
        self.userProfiles = userProfiles
        self.registry_profile = registry_profile
        profile_id = self.userProfiles.get_profile_id(self.registry_profile)
        self.bucket_name = f"{profile_id}-pipeline-registry-bucket"

    def get_file_path(self, pipeline_name: str, version_name: str) -> None:
        """Return file path, with specific folder for each pipeline"""
        return f"{pipeline_name}/pipeline_definition_{version_name}.json"

    def register_version(
        self, pipeline_name: str, json_data: dict, version_name: str
    ) -> None:
        """Register a new Pipeline JSON definition to the registry"""
        file_name = self.get_file_path(pipeline_name, version_name)

        session = boto3.Session(profile_name=self.registry_profile)
        s3 = session.resource("s3")
        s3object = s3.Object(self.bucket_name, file_name)

        s3object.put(Body=(bytes(json.dumps(json_data).encode("UTF-8"))))
        print(f"Saved file '{file_name}' in bucket '{self.bucket_name}'")

    def deploy_pipeline(
        self, profile: str, pipeline_name: str, version_name: str
    ) -> None:
        """Deploys a SageMaker pipeline by creating or updating
        an existing pipeline with the specified name."""

        session = boto3.Session(profile_name=profile)
        sagemaker_client = session.client("sagemaker")
        iam = session.client("iam")
        sagemaker_role = iam.get_role(
            RoleName=f"{self.userProfiles.get_profile_id(profile)}-sagemaker-exec"
        )["Role"]["Arn"]

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
    parser.add_argument("--profile", type=str, default="default", choices=profiles)
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

    pipeline_registry = PipelineRegistry(
        registry_profile=args.registry_profile, userProfiles=userProfiles
    )

    if args.action == "register":
        pipeline = tp.get_pipeline(
            args.pipeline_name,
            userProfiles.get_profile_id(args.profile),
            args.profile,
            args.region,
        )
        pipeline_definition_json = json.loads(pipeline.definition())

        pipeline_registry.register_version(
            pipeline_name=args.pipeline_name,
            json_data=pipeline_definition_json,
            version_name=args.git_commit_hash,
        )
    elif args.action == "deploy":
        pipeline_registry.deploy_pipeline(
            profile=args.profile,
            pipeline_name=args.pipeline_name,
            version_name=args.git_commit_hash,
        )
    elif args.action == "start":
        tp.start_pipeline(args.profile, args.pipeline_name)
