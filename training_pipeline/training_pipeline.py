"""Creates and runs Sagemaker Training Pipeline"""
import json
import os
import argparse
from datetime import datetime

import boto3
from sagemaker.processing import ScriptProcessor
from sagemaker.pytorch.processing import PyTorchProcessor
from sagemaker.workflow.steps import ProcessingStep, TrainingStep
from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.workflow.properties import PropertyFile
from sagemaker.workflow.parameters import ParameterInteger, ParameterFloat
from sagemaker.model_metrics import MetricsSource, ModelMetrics
from sagemaker.workflow.conditions import ConditionGreaterThanOrEqualTo
from sagemaker.workflow.condition_step import ConditionStep
from sagemaker.workflow.functions import JsonGet
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.inputs import TrainingInput
from sagemaker.huggingface import HuggingFaceProcessor, HuggingFace
from sagemaker.huggingface.model import HuggingFaceModel
from sagemaker.workflow.model_step import ModelStep
from sagemaker.workflow.pipeline_experiment_config import PipelineExperimentConfig
from sagemaker.workflow.pipeline_context import PipelineSession
from sagemaker.workflow.steps import CacheConfig

from aws_profiles import UserProfiles


def get_pipeline(pipeline_name: str, profile_name: str, region: str) -> Pipeline:
    session = (
        boto3.Session(profile_name=profile_name) if profile_name else boto3.Session()
    )
    sagemaker_session = PipelineSession(boto_session=session)
    account_id = session.client("sts").get_caller_identity().get("Account")

    iam = session.client("iam")
    role = iam.get_role(RoleName=f"{account_id}-sagemaker-exec")["Role"]["Arn"]

    default_bucket = sagemaker_session.default_bucket()

    # Docker images are located in ECR in 'operations' account
    operations_id = UserProfiles().get_profile_id("operations")
    custom_image_uri = (
        f"{operations_id}.dkr.ecr.{region}.amazonaws.com/training-image:latest"
    )

    model_path = f"s3://{default_bucket}/model"
    data_path = f"s3://{default_bucket}/data"
    model_package_group_name = f"{pipeline_name}ModelGroup"
    model_package_group_arn = (
        f"arn:aws:sagemaker:{region}:{account_id}:"
        f"model-package/{model_package_group_name}"
    )

    gpu_instance_type = "ml.g4dn.xlarge"
    cpu_instance_type = "ml.m5.large"

    pytorch_version = "1.9.0"
    transformers_version = "4.11.0"
    py_version = "py38"
    requirement_dependencies = ["images/train/requirements.txt"]

    cache_config = CacheConfig(enable_caching=False, expire_after="30d")

    trial_name = "trial-run-" + datetime.now().strftime("%d-%m-%Y--%H-%M-%S")
    pipeline_experiment_config = PipelineExperimentConfig(pipeline_name, trial_name)

    # ======================================================
    # Define Pipeline Parameters
    # ======================================================

    epoch_count = ParameterInteger(name="epochs", default_value=1)
    batch_size = ParameterInteger(name="batch_size", default_value=10)
    learning_rate = ParameterFloat(name="learning_rate", default_value=1e-5)

    # ======================================================
    # Step 1: Load and preprocess the data
    # ======================================================

    script_preprocess = PyTorchProcessor(
        framework_version="1.8",
        instance_type=cpu_instance_type,
        image_uri=custom_image_uri,
        instance_count=1,
        base_job_name="preprocess-script",
        role=role,
        sagemaker_session=sagemaker_session,
    )

    preprocess_step_args = script_preprocess.run(
        inputs=[
            ProcessingInput(
                source=os.path.join(data_path, "train.csv"),
                destination="/opt/ml/processing/input/train",
            ),
            ProcessingInput(
                source=os.path.join(data_path, "test.csv"),
                destination="/opt/ml/processing/input/test",
            ),
            ProcessingInput(
                source=os.path.join(data_path, "val.csv"),
                destination="/opt/ml/processing/input/val",
            ),
        ],
        outputs=[
            ProcessingOutput(
                output_name="train", source="/opt/ml/processing/output/train"
            ),
            ProcessingOutput(
                output_name="test", source="/opt/ml/processing/output/test"
            ),
            ProcessingOutput(output_name="val", source="/opt/ml/processing/output/val"),
        ],
        code="preprocess.py",
        source_dir="src",
    )

    step_preprocess = ProcessingStep(
        name="preprocess-data",
        step_args=preprocess_step_args,
        cache_config=cache_config,
    )

    # ======================================================
    # Step 2: Train Huggingface model and optionally finetune hyperparameter
    # ======================================================

    estimator = HuggingFace(
        instance_type=gpu_instance_type,
        instance_count=1,
        source_dir="src",
        entry_point="train.py",
        sagemaker_session=sagemaker_session,
        role=role,
        output_path=model_path,
        transformers_version=transformers_version,
        pytorch_version=pytorch_version,
        py_version=py_version,
        dependencies=requirement_dependencies,
    )

    estimator.set_hyperparameters(
        epoch_count=epoch_count,
        batch_size=batch_size,
        learning_rate=learning_rate,
    )

    step_train = TrainingStep(
        name="train-model",
        estimator=estimator,
        cache_config=cache_config,
        inputs={
            "train": TrainingInput(
                s3_data=step_preprocess.properties.ProcessingOutputConfig.Outputs[
                    "train"
                ].S3Output.S3Uri,
                content_type="text/csv",
            ),
            "test": TrainingInput(
                s3_data=step_preprocess.properties.ProcessingOutputConfig.Outputs[
                    "test"
                ].S3Output.S3Uri,
                content_type="text/csv",
            ),
        },
    )

    # ======================================================
    # Step 3: Evaluate model
    # ======================================================

    script_eval = HuggingFaceProcessor(
        instance_type=gpu_instance_type,
        image_uri=custom_image_uri,
        instance_count=1,
        base_job_name="eval-script",
        role=role,
        sagemaker_session=sagemaker_session,
    )

    evaluation_report = PropertyFile(
        name="EvaluationReport", output_name="evaluation", path="evaluation.json"
    )

    eval_step_args = script_eval.run(
        inputs=[
            ProcessingInput(
                source=step_preprocess.properties.ProcessingOutputConfig.Outputs[
                    "val"
                ].S3Output.S3Uri,
                destination="/opt/ml/processing/val",
            ),
            ProcessingInput(
                source=step_train.properties.ModelArtifacts.S3ModelArtifacts,
                destination="/opt/ml/processing/model",
            ),
        ],
        outputs=[
            ProcessingOutput(
                output_name="evaluation", source="/opt/ml/processing/evaluation"
            ),
        ],
        code="eval.py",
        source_dir="src",
    )

    step_eval = ProcessingStep(
        name="eval-model",
        step_args=eval_step_args,
        property_files=[evaluation_report],
        cache_config=cache_config,
    )

    # ======================================================
    # Step 4: Register model
    # ======================================================

    evaluation_s3_uri = "{}/evaluation.json".format(
        step_eval.arguments["ProcessingOutputConfig"]["Outputs"][0]["S3Output"]["S3Uri"]
    )

    model_metrics = ModelMetrics(
        model_statistics=MetricsSource(
            s3_uri=evaluation_s3_uri,
            content_type="application/json",
        )
    )

    model = HuggingFaceModel(
        name="text-classification-model",
        model_data=step_train.properties.ModelArtifacts.S3ModelArtifacts,
        sagemaker_session=sagemaker_session,
        source_dir="src",
        entry_point="model.py",
        dependencies=requirement_dependencies,
        role=role,
        transformers_version=transformers_version,
        pytorch_version=pytorch_version,
        py_version=py_version,
    )

    step_register = ModelStep(
        name="register-model",
        step_args=model.register(
            content_types=["text/csv"],
            response_types=["text/csv"],
            inference_instances=[gpu_instance_type, "ml.m5.large"],
            transform_instances=[gpu_instance_type, "ml.m5.large"],
            model_package_group_name=model_package_group_name,
            model_metrics=model_metrics,
        ),
    )

    # ======================================================
    # Step 5: Approve model
    # ======================================================

    script_approve = ScriptProcessor(
        command=["python3"],
        image_uri=custom_image_uri,
        instance_type=cpu_instance_type,
        instance_count=1,
        base_job_name="script-approve",
        role=role,
        env={
            "model_package_version": step_register.properties.ModelPackageVersion.to_string(),
            "model_package_group_arn": model_package_group_arn,
        },
        sagemaker_session=sagemaker_session,
    )

    step_approve = ProcessingStep(
        name="approve-model",
        step_args=script_approve.run(
            code="src/approve.py",
        ),
    )

    # ======================================================
    # Step 6: Condition for model approval status
    # ======================================================

    cond_gte = ConditionGreaterThanOrEqualTo(
        left=JsonGet(
            step_name=step_eval.name,
            property_file=evaluation_report,
            json_path="metrics.accuracy.value",
        ),
        right=0.1,
    )

    step_cond = ConditionStep(
        name="accuracy-check",
        conditions=[cond_gte],
        if_steps=[step_approve],
        else_steps=[],
    )

    # ======================================================
    # Final Step: Define Pipeline
    # ======================================================

    pipeline = Pipeline(
        name=pipeline_name,
        parameters=[
            epoch_count,
            batch_size,
            learning_rate,
        ],
        steps=[
            step_preprocess,
            step_train,
            step_register,
            step_eval,
            step_cond,
        ],
        sagemaker_session=sagemaker_session,
        pipeline_experiment_config=pipeline_experiment_config,
    )

    return pipeline


def create_pipeline(pipeline_name, profile, region):
    """Create/update pipeline"""
    pipeline = get_pipeline(
        pipeline_name=pipeline_name,
        profile_name=profile,
        region=region,
    )
    json.loads(pipeline.definition())

    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    account_id = session.client("sts").get_caller_identity().get("Account")
    iam = session.client("iam")
    role = iam.get_role(RoleName=f"{account_id}-sagemaker-exec")["Role"]["Arn"]
    pipeline.upsert(role_arn=role)


def run_pipeline(pipeline_name: str, profile_name: str = None) -> None:
    session = (
        boto3.Session(profile_name=profile_name) if profile_name else boto3.Session()
    )
    sagemaker_client = session.client("sagemaker")
    sagemaker_client.start_pipeline_execution(PipelineName=pipeline_name)


if __name__ == "__main__":
    userProfiles = UserProfiles()
    profiles = userProfiles.list_profiles()

    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=str, default=None, choices=profiles)
    parser.add_argument("--region", type=str, default="eu-west-3")
    parser.add_argument("--pipeline-name", type=str, default="training-pipeline")
    parser.add_argument("--action", type=str, choices=["create", "run"])
    args = parser.parse_args()

    if args.action == "create":
        create_pipeline(args.pipeline_name, args.profile, args.region)

    elif args.action == "run":
        run_pipeline(args.pipeline_name, args.profile)
