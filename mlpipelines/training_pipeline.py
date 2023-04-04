import boto3
import sagemaker.session
import json
import os
import argparse

from sagemaker.processing import ScriptProcessor, FrameworkProcessor
from sagemaker.workflow.steps import ProcessingStep, TrainingStep, TuningStep
from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.workflow.properties import PropertyFile
from sagemaker.workflow.parameters import ParameterInteger, ParameterFloat
from sagemaker.model_metrics import MetricsSource, ModelMetrics
from sagemaker.workflow.conditions import ConditionGreaterThanOrEqualTo
from sagemaker.workflow.condition_step import ConditionStep
from sagemaker.workflow.functions import JsonGet
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.step_collections import RegisterModel
from sagemaker.estimator import Estimator
from sagemaker.inputs import TrainingInput
from sagemaker.model import Model
from sagemaker import PipelineModel
from sagemaker.workflow.steps import CacheConfig
from sagemaker.huggingface import HuggingFaceProcessor, HuggingFace
from sagemaker.huggingface.model import HuggingFaceModel
from sagemaker.workflow.pipeline_context import LocalPipelineSession
from sagemaker.workflow.model_step import ModelStep
from sagemaker.tuner import IntegerParameter, CategoricalParameter, ContinuousParameter, HyperparameterTuner

from sagemaker.workflow.pipeline_context import PipelineSession


parser = argparse.ArgumentParser()
parser.add_argument('--account', type=str, default="101436505502")
parser.add_argument('--region', type=str, default="eu-west-3")
parser.add_argument('--pipeline_name', type=str, default="training-pipeline")
args = parser.parse_args()

region = boto3.Session(region_name=args.region).region_name

sagemaker_session = PipelineSession()
# sagemaker_session = LocalPipelineSession()


# try:
#     role = sagemaker.get_execution_role()
# except ValueError:

iam = boto3.client("iam")
role = iam.get_role(RoleName=f"{args.account}-sagemaker-exec")['Role']['Arn']

default_bucket = sagemaker_session.default_bucket()
train_image_uri = f"{args.account}.dkr.ecr.{args.region}.amazonaws.com/training-image:latest"
# inference_image_uri = f"{args.account}.dkr.ecr.{args.region}.amazonaws.com/inference-image:latest"

model_path = f"s3://{default_bucket}/model"
data_path = f"s3://{default_bucket}/data"
model_package_group_name = f"{args.pipeline_name}ModelGroup"
pipeline_name = args.pipeline_name

gpu_instance_type = "ml.g4dn.xlarge"
pytorch_version = "1.9.0"
transformers_version = "4.11.0"
py_version = "py38"
requirement_dependencies = ['images/inference/requirements.txt']

cache_config = CacheConfig(enable_caching=True, expire_after="30d")

# ------------ Pipeline Parameters ------------

epoch_count = ParameterInteger(
    name="epochs",
    default_value=2
)
batch_size = ParameterInteger(
    name="batch_size",
    default_value=10
)

learning_rate = ParameterFloat(
    name="learning_rate",
    default_value=5e-5
)

# ------------ Preprocess ------------

script_preprocess = HuggingFaceProcessor(
    instance_type=gpu_instance_type,
    image_uri=train_image_uri,
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
    ],
    outputs=[
        ProcessingOutput(output_name="train",
                         source="/opt/ml/processing/output/train"),
        ProcessingOutput(output_name="test",
                         source="/opt/ml/processing/output/test"),
        ProcessingOutput(output_name="labels",
                         source="/opt/ml/processing/output/labels"),

    ],
    code="preprocess.py",
    source_dir="src",
)

step_preprocess = ProcessingStep(
    name="preprocess-data",
    step_args=preprocess_step_args,
    cache_config=cache_config,
)

# ------------ Train ------------

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
    # learning_rate=learning_rate,
)

hyperparameter_ranges = {
    "learning_rate": ContinuousParameter(1e-5, 0.1),
    # "batch-size": CategoricalParameter([32, 64, 128, 256, 512]),
}
objective_metric_name = "average test f1"
objective_type = "Maximize"
metric_definitions = [{"Name": "average test f1",
                       "Regex": "Test set: Average f1: ([0-9\\.]+)"}]

tuner = HyperparameterTuner(
    estimator,
    objective_metric_name,
    hyperparameter_ranges,
    metric_definitions,
    max_jobs=9,
    max_parallel_jobs=1,
    objective_type=objective_type,
)

# step_train = TrainingStep(
#     name="train-model",
#     estimator=estimator,
#     cache_config=cache_config,
#     inputs={
#         "train": TrainingInput(
#             s3_data=step_preprocess.properties.ProcessingOutputConfig.Outputs[
#                 "train"].S3Output.S3Uri,
#             content_type="text/csv",
#         ),
#         "test": TrainingInput(
#             s3_data=step_preprocess.properties.ProcessingOutputConfig.Outputs[
#                 "test"].S3Output.S3Uri,
#             content_type="text/csv",
#         ),
#         "labels": TrainingInput(
#             s3_data=step_preprocess.properties.ProcessingOutputConfig.Outputs[
#                 "labels"].S3Output.S3Uri,
#             content_type="text/csv",
#         )
#     },
# )

step_train = TuningStep(
    name="tune-model",
    cache_config=cache_config,
    step_args=tuner.fit(
        inputs={
            "train": TrainingInput(
                s3_data=step_preprocess.properties.ProcessingOutputConfig.Outputs[
                    "train"].S3Output.S3Uri,
                content_type="text/csv",
            ),
            "test": TrainingInput(
                s3_data=step_preprocess.properties.ProcessingOutputConfig.Outputs[
                    "test"].S3Output.S3Uri,
                content_type="text/csv",
            ),
            "labels": TrainingInput(
                s3_data=step_preprocess.properties.ProcessingOutputConfig.Outputs[
                    "labels"].S3Output.S3Uri,
                content_type="text/csv",
            )
        },
    ),
)

# ------------ Eval ------------

script_eval = HuggingFaceProcessor(
    instance_type=gpu_instance_type,
    image_uri=train_image_uri,
    instance_count=1,
    base_job_name="eval-script",
    role=role,
    sagemaker_session=sagemaker_session,
)

evaluation_report = PropertyFile(
    name="EvaluationReport",
    output_name="evaluation",
    path="evaluation.json"
)

eval_step_args = script_eval.run(
    inputs=[
        ProcessingInput(
            source=step_preprocess.properties.ProcessingOutputConfig.Outputs[
                "test"
            ].S3Output.S3Uri,
            destination="/opt/ml/processing/test",
        ),
        ProcessingInput(
            # source=step_train.properties.ModelArtifacts.S3ModelArtifacts,
            source=step_train.get_top_model_s3_uri(
                top_k=0, s3_bucket=sagemaker_session.default_bucket()),
            destination="/opt/ml/processing/model",
        ),
        ProcessingInput(
            source=step_preprocess.properties.ProcessingOutputConfig.Outputs[
                "labels"].S3Output.S3Uri,
            destination="/opt/ml/processing/labels",
        ),
    ],
    outputs=[
        ProcessingOutput(output_name="evaluation",
                         source="/opt/ml/processing/evaluation"),
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

# ------------ Register ------------

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
    # model_data=step_train.properties.ModelArtifacts.S3ModelArtifacts,
    model_data=step_train.get_top_model_s3_uri(
        top_k=0,
        s3_bucket=sagemaker_session.default_bucket()
    ),
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
        inference_instances=[gpu_instance_type, gpu_instance_type],
        transform_instances=[gpu_instance_type],
        model_package_group_name=model_package_group_name,
        model_metrics=model_metrics,
    )
)

# ------------ Deploy (not used in pipeline) ------------

script_deploy = ScriptProcessor(
    image_uri=train_image_uri,
    command=["python3"],
    instance_type="ml.t3.medium",
    instance_count=1,
    base_job_name="script-workshop-deploy",
    role=role,
)

step_deploy = ProcessingStep(
    name="workshop-deploy-model",
    processor=script_deploy,
    inputs=[],
    outputs=[],
    code="src/deploy.py",
    property_files=[],
)


# ------------ Condition ------------

cond_gte = ConditionGreaterThanOrEqualTo(
    left=JsonGet(
        step_name=step_eval.name,
        property_file=evaluation_report,
        json_path="metrics.accuracy.value"
    ),
    right=0.1
)

step_cond = ConditionStep(
    name="accuracy-check",
    conditions=[cond_gte],
    if_steps=[step_register],
    else_steps=[],
)

#  ------------ build Pipeline ------------

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
        step_eval,
        step_cond,
    ],
    sagemaker_session=sagemaker_session,
    pipeline_experiment_config=None,
)


if __name__ == '__main__':
    json.loads(pipeline.definition())
    pipeline.upsert(role_arn=role)
    execution = pipeline.start()
    execution = execution.wait()
