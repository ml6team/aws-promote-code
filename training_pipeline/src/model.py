"""Inference Code for model"""
import os
import sys
import json
import logging
import pandas as pd
from io import StringIO
from tqdm import tqdm

import torch
from torch.utils.data import DataLoader

from utils.ml_pipeline_components import get_model, MyTokenizer, MyDataset
from utils import config

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


def input_fn(input_data, content_type):
    """Parse input data payload"""
    logger.info("input_fn")
    if content_type == "application/json":
        input_dict = json.loads(input_data)
        return input_dict["instances"]
    elif content_type == "text/csv":
        df = pd.read_csv(StringIO(input_data), sep=",")
        inputs = df["transcription"].tolist()
        return inputs
    else:
        raise ValueError("{} not supported by script!".format(content_type))


def output_fn(prediction, accept):
    """Format prediction output"""
    logger.info("output_fn")
    if accept == "application/json":
        return {"prediction": prediction}
    elif accept == "text/csv":
        return prediction
    else:
        raise RuntimeError(
            "{} accept type is not supported by this script.".format(accept)
        )


def predict_fn(input_data, model):
    """Process input data"""
    logger.info("predict_fn")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Device: {device}")

    model.eval()
    model.to(device)
    tok = MyTokenizer()
    input = tok.tokenizer(
        input_data, padding="max_length", return_tensors="pt", truncation=True
    )

    dataset = MyDataset(input.input_ids, input.attention_mask)
    dataloader = DataLoader(dataset, shuffle=False, batch_size=10)

    output = []
    for x, _ in tqdm(dataloader):
        outs = model(x.to(device))
        output += torch.argmax(outs.logits.cpu(), dim=1)

    return [config.MEDICAL_CATEGORIES[i.item()] for i in output]


def model_fn(model_dir):
    """Deserialize/load fitted model"""
    logger.info("model_fn")
    model = get_model(num_labels=len(config.MEDICAL_CATEGORIES))
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.load_state_dict(
        torch.load(
            os.path.join(model_dir, "model.joblib"), map_location=torch.device(device)
        )
    )
    return model
