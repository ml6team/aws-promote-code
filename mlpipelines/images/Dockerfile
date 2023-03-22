# FROM python:3.7.9-slim
FROM 763104351884.dkr.ecr.us-east-1.amazonaws.com/pytorch-training:1.9.0-gpu-py38-cu111-ubuntu20.04


# Copy requirements first to leverage docker cache
COPY images/requirements.txt .
RUN pip install -r requirements.txt
