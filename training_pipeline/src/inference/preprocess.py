import json
import joblib
import os

from sagemaker_containers.beta.framework import worker, encoders


def input_fn(input_data, content_type):
    """Parse input data payload"""
    if content_type == "application/json":
        input_dict = json.loads(input_data)
        return input_dict["input"]
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
    elif accept == "text/csv":
        return worker.Response(encoders.encode(prediction, accept), mimetype=accept)
    else:
        raise RuntimeError(
            "{} accept type is not supported by this script.".format(accept))


def predict_fn(input_data, model):
    """Preprocess input data"""
    return model.transform(input_data)


def model_fn(model_dir):
    """Deserialize/load fitted model"""
    return joblib.load(os.path.join(model_dir, "model.joblib"))
