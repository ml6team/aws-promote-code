"""Implements Pipeline Registry on top of AWS S3-bucket"""
import json
import argparse

import boto3
from sagemaker.workflow.pipeline_context import PipelineSession

import training_pipeline as tp


class PipelineRegistry:
    def __init__(self) -> None:
        self.sagemaker_session = PipelineSession()
        self.bucket_name = self.sagemaker_session.default_bucket()
        self.pipeline_name = "TestPipe1"

        self.REGISTRY_FOLDER_NAME = "training_pipeline_registry"
        self.sagemaker_client = boto3.client("sagemaker")

        iam = boto3.client("iam")
        self.sagemaker_role = iam.get_role(RoleName=f"{args.account}-sagemaker-exec")[
            "Role"
        ]["Arn"]

    def get_file_path(self, version_name):
        return f"{self.REGISTRY_FOLDER_NAME}/training_pipeline_{version_name}.json"

    def register_version(self, json_data, version_name):
        # TODO: add git commits and environment tags to version pipeline
        file_name = self.get_file_path(version_name)

        s3 = boto3.resource("s3")
        s3object = s3.Object(self.bucket_name, file_name)

        s3object.put(Body=(bytes(json.dumps(json_data).encode("UTF-8"))))
        print(f"Saved file '{file_name}' in bucket '{self.bucket_name}'")

    def load_version(self, version_name):
        s3 = boto3.resource("s3")
        file_name = self.get_file_path(version_name)
        s3object = s3.Object(self.bucket_name, file_name)
        return json.loads(s3object.get()["Body"].read())

    def create_pipeline(self, version_name):
        """Create pipeline directly from S3 location"""
        response = self.sagemaker_client.create_pipeline(
            PipelineName=self.pipeline_name,
            RoleArn=self.sagemaker_role,
            PipelineDefinitionS3Location={
                "Bucket": self.bucket_name,
                "ObjectKey": self.get_file_path(version_name),
            },
        )
        print(response)

    def update_pipeline(self, version_name):
        """Updates pipeline by first deleting old pipeline and then creating new one"""
        self.sagemaker_client.delete_pipeline(
            PipelineName=self.pipeline_name,
            # ClientRequestToken='string'
        )
        self.create_pipeline(version_name)

    def start_pipeline(
        self,
    ):
        self.sagemaker_client.start_pipeline_execution(PipelineName=self.pipeline_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--action",
        type=str,
        choices=["register_version", "create", "update", "start"],
        default="push",
    )
    parser.add_argument("--account", type=str, default="101436505502")
    parser.add_argument("--region", type=str, default="eu-west-3")
    parser.add_argument("--pipeline-name", type=str, default="training-pipeline")
    parser.add_argument(
        "--git-commit-hash",
        type=str,
        default="ffac537e6cbbf934b08745a378932722df287a53",
    )  # dummy for now

    args = parser.parse_args()

    pipeline_registry = PipelineRegistry()

    if args.action == "register_version":
        pipeline = tp.get_pipeline(args.pipeline_name, args.account, args.region)
        pipeline_definition_json = json.loads(pipeline.definition())
        pipeline_registry.register_version(
            pipeline_definition_json, args.git_commit_hash
        )
    elif args.action == "create":
        pipeline_registry.create_pipeline(args.git_commit_hash)
    elif args.action == "update":
        pipeline_registry.update_pipeline(args.git_commit_hash)
    elif args.action == "start":
        pipeline_registry.start_pipeline()
