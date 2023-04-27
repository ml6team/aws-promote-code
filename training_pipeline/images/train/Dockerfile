FROM 763104351884.dkr.ecr.eu-west-3.amazonaws.com/pytorch-training:1.9.0-gpu-py38-cu111-ubuntu20.04

# Copy requirements
COPY images/train/requirements.txt .
RUN pip install -r requirements.txt
