# FROM python:3.7.9-slim
# FROM 763104351884.dkr.ecr.us-east-1.amazonaws.com/pytorch-training:1.9.0-gpu-py38-cu111-ubuntu20.04
FROM 763104351884.dkr.ecr.eu-west-3.amazonaws.com/pytorch-training:1.9.0-gpu-py38-cu111-ubuntu20.04

# FROM 763104351884.dkr.ecr.eu-west-3.amazonaws.com/huggingface-pytorch-training:1.13.1-transformers4.26.0-gpu-py39-cu117-ubuntu20.04


# Copy requirements
COPY images/train/requirements.txt .
RUN pip install -r requirements.txt
