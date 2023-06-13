# AWS Artifact - Manual setup for running the training pipeline in the dev environment

## Introduction

In this SageMaker pipeline a pre-trained [Huggingface BERT-model](https://huggingface.co/distilbert-base-uncased) is fine-tuned on a **text-classification task** of [Medical Transcriptions](https://www.kaggle.com/datasets/tboyle10/medicaltranscriptions). This dataset was chosen because medical data often contains sensitive information and one of the benefits of promoting code instead of models is that the production data is not needed in the dev environment. The table bellow shows some examples of the dataset:

| class (target) | description (input) |
| --------------- | --------------- |
| Surgery | PROCEDURE PERFORMED:  ,DDDR permanent pacemaker.,INDICATION: , Tachybrady syndrome.,PROCEDURE:,  After all risks, benefits, and alternatives of the procedure were explained in detail to the patient, informed consent was obtained both verbally and in writing ... |
| Obstetrics / Gynecology | DELIVERY NOTE:,  This G1, P0 with EDC 12/23/08 presented with SROM about 7.30 this morning.  Her prenatal care complicated by GBS screen positive and a transfer of care at 34 weeks from Idaho.  Exam upon arrival 2 to 3 cm, 100% effaced, -1 ...  |
| Cardiovascular / Pulmonary | 2-D M-MODE: , ,1.  Left atrial enlargement with left atrial diameter of 4.7 cm.,2.  Normal size right and left ventricle .,3.  Normal LV systolic function with left ventricular ejection fraction of 51%.,4.  Normal LV diastolic function.,5.  No pericardial effusion ... |

In total there are 40 different classes:
```
['Allergy / Immunology',  'Autopsy',  'Bariatrics',  'Cardiovascular / Pulmonary',  'Chiropractic',  'Consult - History and Phy.',  'Cosmetic / Plastic Surgery',  'Dentistry', 'Dermatology', 'Diets and Nutritions', 'Discharge Summary', 'ENT - Otolaryngology', 'Emergency Room Reports', 'Endocrinology', 'Gastroenterology', 'General Medicine', 'Hematology - Oncology', 'Hospice - Palliative Care', 'IME-QME-Work Comp etc.', 'Lab Medicine - Pathology', 'Letters', 'Nephrology', 'Neurology', 'Neurosurgery', 'Obstetrics / Gynecology', 'Office Notes', 'Ophthalmology', 'Orthopedic', 'Pain Management', 'Pediatrics - Neonatal', 'Physical Medicine - Rehab', 'Podiatry', 'Psychiatry / Psychology', 'Radiology', 'Rheumatology', 'SOAP / Chart / Progress Notes', 'Sleep Medicine', 'Speech - Language', 'Surgery', 'Urology']
```

This README describes the manual setup of the SageMaker pipeline and all needed artifacts in the **development** (dev) environment.

**!! NOTE !!** General setup steps for the different accounts (dev, staging, prod, operations) from the main [README](../README.md) need to be performed before following these steps.

# 1. Setup

Our resources for the dev environment were already created in the main setup, which means we only need to install some requirements before we can begin:
```
pip install -r requirements.txt
```

# 2. Upload the data
The  medical dataset is split and uploaded to a S3-bucket and will be used as input to the training pipeline. Do this by running the following command:
```
python upload_dataset.py --profile dev
```
If you don't provide a specific bucket name (via the flag `--bucket-name`), the **Sagemaker Default bucket** is chosen as the location of your training data.

# 3. Build custom Docker image

Some of the steps in our training-pipeline require specific Docker images. Additionally we need a Docker image for the Lambda function which executes our [automatic model deployment](#5-model-deployment). The following command builds and pushes both those images to the AWS Elastic-Container-Registry (ECR) on our *operations* account. Run the shell script from the `/training_pipeline` folder:
```bash
sh images/build_and_push_all.sh
```

The script automatically pulls the Account-ID of the *operations* account from the `profiles.conf` file and uses it to specify the account where the ECR is located.

# 4. Creating and running the pipeline

To create the training pipeline, execute:
```
python training_pipeline.py --profile dev --action create
```

To start a run of the training pipeline, execute:
```
python training_pipeline.py --profile dev --action run
```

In both commands we use the `--profile` flag to specify which account from our config file we want to create/run our pipeline in.

## The training pipeline steps are described in detail in the following table:

| Nr | Step name | Description |
| --------------- | --------------- | --------------- |
| 1 | preprocess-data | The training and test data is loaded from the S3 bucket as Pandas DataFrames. The column 'transcription' is the text training input and is tokenized with the Huggingface [AutoTokenizer](https://huggingface.co/docs/transformers/model_doc/auto#transformers.AutoTokenizer). The column 'medical_specialty' is the classification target and is encoded numerically. Both training and test data are saved as NumPy Arrays to the S3 bucket and made available to other pipeline steps as input.|
| 2 | train-model | The pre-trained [Huggingface BERT model](https://huggingface.co/distilbert-base-uncased) is fine-tuned on the training data. The Training and Test data are loaded as a PyTorch Dataset. For training the 'AdamW' optimizer with a learning rate of '1e-5' is used, the model is evaluated on the test data every epoch and the metrics are tracked with SageMaker Experiments. After training the model weights are saved to the S3 bucket.|
| 3 | register-model | Every trained model is registered to the SageMaker Model Registry in a Model Group. |
| 4 | eval-model | After training the model is evaluated on the test data and the results are used for the accuracy check. If the prerequisites are meet the 'approve-model' step is run.|
| 5 | approve-model | The model status of the registered model in the Model Group is updated to 'approved' and now can be used to deploy a Model endpoint or for a Batch Transformation Job.|


![Training Pipeline Image](/readme_images/training_pipeline.png)

The status of the pipeline run can be tracked inside the Sagemaker Studio **Pipelines**. Also under **Experiments** the training and test metrics are tracked and can be displayed as Graphs.

# 5. Model deployment

For automatic model deployment every time a new model is registered and approved, a **AWS Lambda** function is triggered by a **AWS EventBridge rule** which either creates or updates a SageMaker endpoint. You can also deploy a registered model-version manually by running the following command. Keep in mind that only models which have been approved can be deployed.
```
python deploy.py --profile dev --model-version 1
```
Alternatively you can run without providing a model version and the latest approved model will be picked automatically:
```
python deploy.py --profile dev
```

# 6. Model inference

For testing model inference the Notebook `training_pipeline/test.ipynb` is used. There the model inference for single inputs, but also for batch-inference can be tested.

# 7. Automatic retraining
It is common to retrain Machine Learning models after a certain time or if certain measures indicate a decrease in prediction quality. In this project automatic retraining is simply triggered every week. This is done by a **AWS EventBridge Schedule** and is by default only enabled in the *production* account.

# Contributing

We use [poetry](https://python-poetry.org/docs/) and [pre-commit](https://pre-commit.com/) to 
enable a smooth developer flow. Run the following commands to set up your development environment:

```commandline
pip install poetry
poetry install
pre-commit install
```