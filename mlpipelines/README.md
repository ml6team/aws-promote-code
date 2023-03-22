# Sagemaker Boilerplate

## Introduction

This boilerplate shows how to get started with Sagemaker Pipelines. The main objective of this boilerplate is to provide an example pipeline setup, based on which the user can integrate its own code and logic.


## Using the pipeline

### Getting started

To get started, prepare all the resources that need to be created by applying the generated Terraform configuration. You can do this by running the following command from within the `terraform/main` folder:
```
terraform apply --var-file ../environment/project.tfvars
```

After this, install the requirements by running:
```
pip install -r requirements.txt
```

### Build docker image

Each pipeline step requires a base docker image. You can use prebuild Images from Sagemaker or you can build your own. Here we can build our own image by running:

```bash
sh images/build_and_push.sh
```

### Running the pipeline

To run your pipeline, start the pipeline job of `your-pipeline-name.py` via:
```
python <your-pipeline-name>.py
```

The example pipeline trains a dummy model and pushes the model to the AWS model registry. 


### Model deployment

You can deploy the model by running:
```
python deploy.py
```

The script will first approve and then deploy a model which was pushed to the model registry. 

