# AWS Artifact - Training-Pipeline

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
The train and test data is split and uploaded to the Sagemaker S3 default bucket and will be used to run the training pipeline. Do this by running the following command:
```
python upload_dataset.py
```

## 3. Build custom docker image

Some of the pipeline steps require a base docker image. You can use pre-build Images from Sagemaker or you can build your own. By running the following command, we build and register our own image to AWS Elastic Container Registry (ECR):

```bash
sh images/train/build_and_push.sh
```

## 4. Running the pipeline

To run the training pipeline, start the pipeline job with:
```
python training_pipeline.py
```

The training pipeline steps are described in detail in the following table:

| Nr | Step name | Description |
| --------------- | --------------- | --------------- |
| 1 | preprocess-data | The training and test data is loaded from the S3 bucket as Pandas DataFrames. The column 'transcription' is the text training input and is tokenized with the Huggingface [AutoTokenizer](https://huggingface.co/docs/transformers/model_doc/auto#transformers.AutoTokenizer). The column 'medical_specialty' is the classification target and is encoded numerically. Both training and test data are saved as NumPy Arrays to the S3 bucket and made available to other pipeline steps as input.|
| 2 | train-model | The pre-trained [Huggingface BERT model](https://huggingface.co/distilbert-base-uncased) is fine-tuned on the training data. The Training and Test data are loaded as a PyTorch Dataset. For training the 'AdamW' optimizer with a learning rate of '1e-5' is used, the model is evaluated on the test data every epoch and the metrics are tracked with SageMaker Experiments. After training the model weights are saved to the S3 bucket.|
| 3 | register-model | Every trained model is registered to the SageMaker Model Registry in a Model Group. |
| 4 | eval-model | After training the model is evaluated on the test data and the results are used for the accuracy check. If the prerequisites are meet the 'approve-model' step is run.|
| 5 | approve-model | The model status of the registered model in the Model Group is updated to 'approved' and now can be used to deploy a Model endpoint or for a Batch Transformation Job.|


![Training Pipeline Image](/readme_images/training_pipeline.png)

The status of the pipeline run can be tracked inside the Sagemaker Studio **Pipelines**. Also under **Experiments** the training and test metrics are tracked and can be displayed as Graphs.

## 5. Model deployment

You can deploy a registered model version by running the following command. Keep in mind that only models which have been approved can be deployed.
```
python deploy.py --model-version 1
```
Alternatively you can run without providing a model version and the latest approved model will be picked automatically:
```
python deploy.py
```

The model is deployed as a Sagemaker Endpoint.

## 6. Model inference

For testing model inference the Notebook `test.ipynb` is used. There the model inference for single inputs, but also for batch-inference can be tested.

