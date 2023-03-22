"""Inference Code for model"""
import os
import json

import torch
from sagemaker_containers.beta.framework import worker, encoders

from utils.helper import get_model, MyTokenizer
from utils import config


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
    tokenizer = MyTokenizer()
    input = tokenizer(input_data, return_tensors='pt')
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    input.to(device)
    outputs = model(**input)
    y_pred = torch.argmax(outputs.logits.cpu(), dim=1)
    return [config.MEDICAL_CATEGORIES[i.item()] for i in y_pred]



def model_fn(model_dir):
    """Deserialize/load fitted model"""
    model = get_model(num_labels=40)
    model.load_state_dict(torch.load(os.path.join(model_dir, "model.joblib")))
    return model
