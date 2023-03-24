# AWS Artifcat - Training-Pipeline

## Introduction

This pipeline was created with the Nimbus boilerplate tool. 

## 1. Generate resources

To get started, prepare all the resources that need to be created by applying the generated Terraform configuration. You can do this by running the following command from within the `terraform/main` folder:
```
terraform apply --var-file ../environment/project.tfvars
```

After this, install the requirements by running:
```
pip install -r requirements.txt
```

## 2. Upload the data
The train and test data is uploaded to the Sagemaker S3 default bucket and can then be used to run the pipeline.
```
python upload_dataset.py
```

## 3. Build docker image

Each pipeline step requires a base docker image. You can use prebuild Images from Sagemaker or you can build your own. Here we can build and register our own training and inference image by running:

```bash
sh images/train/build_and_push.sh
sh images/inference/build_and_push.sh

```

## 4. Running the pipeline

To run your pipeline, start the pipeline job of `training_pipeline.py` via:
```
python training_pipeline.py
```

The training pipeline trains a model and pushes the model to the AWS model registry, if it achieves a certain accuracy.

## 5. Model deployment

You can deploy the model by running:
```
python deploy.py
```

The script will first approve and then deploy a model which was pushed to the model registry. 

