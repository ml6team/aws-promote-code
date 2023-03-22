import os
import json
import logging
import joblib

import torch
from sagemaker_containers.beta.framework import worker, encoders
from transformers import AutoModelForSequenceClassification, AutoTokenizer

model_name = "distilbert-base-uncased"


def input_fn(input_data, content_type):
    """Parse input data payload"""
    if content_type == "application/json":
        input_dict = json.loads(input_data)
        return input_dict["instances"]
    else:
        raise ValueError("{} not supported by script!".format(content_type))


def output_fn(prediction, accept):
    """Format prediction output"""
    if accept == "application/json":
        instances = []
        for row in prediction.tolist():
            instances.append(row)
        json_output = {"instances": instances}

        return worker.Response(json.dumps(json_output), mimetype=accept)
    else:
        raise RuntimeError(
            "{} accept type is not supported by this script.".format(accept))


def predict_fn(input_data, model):
    """Process input data"""
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    input = tokenizer(input_data, return_tensors='pt')
    return model(**input)


def model_fn(model_dir):
    """Deserialize/load fitted model"""
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=40,
    )
    model.load_state_dict(torch.load(os.path.join(model_dir, "model.joblib")))
    return model
