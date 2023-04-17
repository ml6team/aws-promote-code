# AWS Artifcat - Training-Pipeline

## Introduction

This Sagemaker training-pipeline was created with the ML6 Nimbus boilerplate tool. In this training pipeline a pre-trained [Huggingface BERT model](https://huggingface.co/distilbert-base-uncased) is fine-tuned on a text-classification task of [Medical Transcriptions](https://www.kaggle.com/datasets/tboyle10/medicaltranscriptions).

## 1. Generate resources

To get started, prepare all the AWS resources that need to be created by applying the generated Terraform configuration. You can do this by running the following command from within the `terraform/main` folder:
```
terraform apply --var-file ../environment/project.tfvars
```

After this, install the requirements by running:
```
pip install -r requirements.txt
```

## 2. Upload the data
The train and test data is split and uploaded to the Sagemaker S3 default bucket and will be used to run the training pipeline. Do this be running the following command:
```
python upload_dataset.py
```

## 3. Build custom docker image

Some of the pipeline step require a base docker image. You can use pre-build Images from Sagemaker or you can build your own. By running the following command, we build and register our own image to AWS Elastic Container Registry (ECR):

```bash
sh images/train/build_and_push.sh
```

## 4. Running the pipeline

To run your pipeline, start the pipeline job with:
```
python training_pipeline.py
```

The training pipeline preprocesses the data, trains and registers a model and if it achieves a certain accuracy on the test data, will also be approved for deployment.

![Training Pipeline Image](/readme_images/training_pipeline.png)

The status of the pipeline run can be tracked inside the Sagemaker Studio **Pipelines**. Also under **Experiments** the training and test metrics are tracked and can be displayed as Graphs.

## 5. Model deployment

You can deploy a registered model version by running:
```
python deploy.py --model-version 1
```

The script will deploy the model which was pushed to the model registry and was also approved. It is deployed as a Sagemaker Endpoint.

## 6. Model inference

The model inference can be tested with the Notebook `test.ipynb`. There the model inference for single inputs, but also for batch-inference can be tested.

