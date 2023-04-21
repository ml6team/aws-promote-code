""" Pipeline Evaluation Step: The trained model is loaded and evaluated on the eval data"""
import numpy as np
import logging
import json
import pathlib
import tarfile

import torch
from torch.utils.data import DataLoader
from sklearn.metrics import f1_score, accuracy_score

from utils.ml_pipeline_components import load_dataset, get_model
from utils import config


def eval_model():

    dataset = load_dataset("/opt/ml/processing/val", "val")
    dataloader = DataLoader(dataset, shuffle=True, batch_size=10)
    # num_labels = load_num_labels("/opt/ml/processing/labels")
    num_labels = len(config.MEDICAL_CATEGORIES)

    logging.info('Fetching model')
    model = get_model(num_labels)

    model_path = "/opt/ml/processing/model/model.tar.gz"
    with tarfile.open(model_path, "r:gz") as tar:
        tar.extractall("./model")

    model.load_state_dict(torch.load("./model/model.joblib"))

    logging.info('Evaluating model')
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logging.info(f"Training on device: {device}")

    model.eval()
    model.to(device)
    f1_list = []
    acc_list = []
    with torch.no_grad():
        for x, y in dataloader:
            labels = y.long()
            outputs = model(x.to(device), labels=labels.to(device))
            y_pred = torch.argmax(outputs.logits.cpu(), dim=1)
            f1_list.append(f1_score(y, y_pred, average="macro"))
            acc_list.append(accuracy_score(y, y_pred))

    accuracy = np.mean(acc_list)
    logging.info(f"Attained accuracy: {accuracy}")
    report_dict = {
        "metrics": {
            "accuracy": {
                "value": accuracy,
            },
        },
    }

    logging.info('Saving evaluation')
    output_dir = "/opt/ml/processing/evaluation"
    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

    evaluation_path = f"{output_dir}/evaluation.json"
    with open(evaluation_path, "w") as f:
        f.write(json.dumps(report_dict))


if __name__ == "__main__":
    eval_model()
