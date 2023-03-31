# FROM python:3.7.9-slim
FROM 763104351884.dkr.ecr.eu-west-3.amazonaws.com/pytorch-inference:1.13.1-gpu-py39-cu117-ubuntu20.04-sagemaker
# FROM 763104351884.dkr.ecr.eu-west-3.amazonaws.com/pytorch-inference:1.9.0-gpu-py38-cu111-ubuntu20.04
# FROM 763104351884.dkr.ecr.eu-west-3.amazonaws.com/huggingface-pytorch-inference:1.13.1-transformers4.26.0-gpu-py39-cu117-ubuntu20.04

# Copy requirements first to leverage docker cache
# COPY images/train/requirements.txt .
# RUN pip install -r requirements.txt


# ENV PATH="/opt/ml/code:${PATH}"

# COPY /src /opt/ml/code

# ENV SAGEMAKER_SUBMIT_DIRECTORY /opt/ml/code

# ENV SAGEMAKER_PROGRAM model.py

# ENV PATH="/opt/ml/code:${PATH}"

# ENV SAGEMAKER_SUBMIT_DIRECTORY /opt/ml/code
# COPY /src opt/ml/code
