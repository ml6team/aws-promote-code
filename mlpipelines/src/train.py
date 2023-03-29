import numpy as np
import os
import logging
import argparse

import torch
from torch.optim import AdamW
from torch.utils.data import DataLoader
from sklearn.metrics import f1_score, accuracy_score
from transformers import get_scheduler

import boto3
import sagemaker
from sagemaker.session import Session
from sagemaker.experiments.run import Run
from sagemaker.utils import unique_name_from_base


from utils.helper import load_dataset, load_num_labels, get_model


def parse_args():
    logging.info('reading arguments')

    parser = argparse.ArgumentParser()

    # model hyperparameters
    parser.add_argument("--epoch_count", type=int, required=True)
    parser.add_argument("--batch_size", type=int, required=True)

    # data directories
    parser.add_argument('--train', type=str,
                        default=os.environ.get('SM_CHANNEL_TRAIN'))
    parser.add_argument('--labels', type=str,
                        default=os.environ.get('SM_CHANNEL_LABELS'))

    # model directory
    parser.add_argument('--sm-model-dir', type=str,
                        default=os.environ.get('SM_MODEL_DIR'))

    # args = parser.parse_args()
    return parser.parse_known_args()


def train(run):
    args, _ = parse_args()

    logging.info('Load data')
    dataset = load_dataset(args.train, "train")
    num_labels = load_num_labels(args.labels)
    dataloader = DataLoader(dataset, shuffle=True, batch_size=args.batch_size)
    
    logging.info('Training model')
    model = get_model(num_labels)
    optimizer = AdamW(model.parameters(), lr=5e-5)
    
    num_epochs = args.epoch_count
    num_training_steps = num_epochs * len(dataloader)
    lr_scheduler = get_scheduler(
        name="linear", optimizer=optimizer, num_warmup_steps=0, num_training_steps=num_training_steps
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logging.info(f"Training on device: {device}")

    model.train()
    model.to(device)
    counter = 0
    for epoch in range(num_epochs):
        for x, y in dataloader:

            labels = y.long()
            outputs = model(x.to(device), labels=labels.to(device))
            y_pred = torch.argmax(outputs.logits.cpu(), dim=1)
            f1 = f1_score(y, y_pred, average="macro")
            acc = accuracy_score(y, y_pred)

            loss = outputs.loss
            loss.backward()

            optimizer.step()
            lr_scheduler.step()
            optimizer.zero_grad()

            # track
            run.log_metric(name="training-loss", value=loss, step=counter)
            run.log_metric(name="training-accuracy", value=acc, step=counter)
            run.log_metric(name="training-f1", value=f1, step=counter)
            logging.info(f"Training: step {counter}")

            counter += 1

    logging.info('Saving model')
    model_location = os.path.join(args.sm_model_dir, "model.joblib")
    with open(model_location, 'wb') as f:
        torch.save(model.state_dict(), f)

    logging.info("Stored trained model at {}".format(model_location))


if __name__ == "__main__":
    session = Session(boto3.session.Session(region_name="eu-west-3"))
    exp_name = "training-pipeline"
    with Run(
        experiment_name=exp_name,
        run_name=unique_name_from_base(exp_name + "-run"),
        sagemaker_session=session,
    ) as run:
        train(run)
