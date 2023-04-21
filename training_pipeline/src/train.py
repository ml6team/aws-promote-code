""" Pipeline Training Step: The model is trained and the weights are saved. """
import numpy as np
import os
import sys
import logging
import argparse

import torch
from torch.optim import AdamW
from torch.utils.data import DataLoader
from sklearn.metrics import f1_score, accuracy_score
from transformers import get_scheduler

import boto3
from sagemaker.session import Session
from sagemaker.experiments.run import Run
from sagemaker.utils import unique_name_from_base


from utils.ml_pipeline_components import load_dataset, get_model
from utils import config

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


def parse_args():
    logger.info("reading arguments")

    parser = argparse.ArgumentParser()

    # model hyperparameters
    parser.add_argument("--epoch_count", type=int, required=True)
    parser.add_argument("--batch_size", type=int, required=True)
    parser.add_argument("--learning_rate", type=float, required=True)

    # data directories
    parser.add_argument("--train", type=str, default=os.environ.get("SM_CHANNEL_TRAIN"))
    parser.add_argument("--test", type=str, default=os.environ.get("SM_CHANNEL_TEST"))
    # parser.add_argument('--labels', type=str,
    #                     default=os.environ.get('SM_CHANNEL_LABELS'))

    # model directory
    parser.add_argument(
        "--sm-model-dir", type=str, default=os.environ.get("SM_MODEL_DIR")
    )

    # args = parser.parse_args()
    return parser.parse_known_args()


def test_model(model, test_dataloader, device):
    model.eval()
    f1_list = []
    acc_list = []
    with torch.no_grad():
        for x, y in test_dataloader:
            labels = y.long()
            outputs = model(x.to(device), labels=labels.to(device))
            y_pred = torch.argmax(outputs.logits.cpu(), dim=1)
            f1_list.append(f1_score(y, y_pred, average="macro"))
            acc_list.append(accuracy_score(y, y_pred))

    return np.mean(acc_list), np.mean(f1_list)


def train(run):
    args, _ = parse_args()

    log_interval = 100

    logger.info("Load train data")
    train_dataset = load_dataset(args.train, "train")
    train_dataloader = DataLoader(
        train_dataset, shuffle=True, batch_size=args.batch_size
    )

    logger.info("Load test data")
    test_dataset = load_dataset(args.test, "test")
    test_dataloader = DataLoader(test_dataset, shuffle=True, batch_size=args.batch_size)

    logger.info("Training model")
    num_labels = len(config.MEDICAL_CATEGORIES)
    model = get_model(num_labels)
    optimizer = AdamW(model.parameters(), lr=args.learning_rate)

    num_epochs = args.epoch_count
    num_training_steps = num_epochs * len(train_dataloader)
    lr_scheduler = get_scheduler(
        name="linear",
        optimizer=optimizer,
        num_warmup_steps=0,
        num_training_steps=num_training_steps,
    )

    run.log_parameters(
        {
            "epoch_count": args.epoch_count,
            "batch_size": args.batch_size,
            "learning_rate": args.learning_rate,
        }
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Training on device: {device}")

    model.to(device)
    counter = 0
    train_loss_ = 0.0
    train_acc_ = 0.0
    train_f1_ = 0.0

    for epoch in range(num_epochs):
        model.train()
        for x, y in train_dataloader:
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
            if counter % log_interval == 0:
                run.log_metric(
                    name="training-loss", value=train_loss_ / log_interval, step=counter
                )
                run.log_metric(
                    name="training-accuracy",
                    value=train_acc_ / log_interval,
                    step=counter,
                )
                run.log_metric(
                    name="training-f1", value=train_f1_ / log_interval, step=counter
                )
                logger.info(f"Training: step {counter}")

                train_loss_ = 0.0
                train_acc_ = 0.0
                train_f1_ = 0.0

            train_loss_ += loss
            train_acc_ += acc
            train_f1_ += f1
            counter += 1

        # test model
        test_acc, test_f1 = test_model(model, test_dataloader, device)
        logger.info(f"Test set: Average f1: {test_f1:.4f}")
        run.log_metric(name="test-accuracy", value=test_acc, step=counter)
        run.log_metric(name="test-f1", value=test_f1, step=counter)

    logger.info("Saving model")
    model_location = os.path.join(args.sm_model_dir, "model.joblib")
    with open(model_location, "wb") as f:
        torch.save(model.state_dict(), f)

    logger.info("Stored trained model at {}".format(model_location))


if __name__ == "__main__":
    session = Session(boto3.session.Session(region_name="eu-west-3"))
    exp_name = "training-pipeline"

    # TODO: load run which is automatically create by sagemaker session
    # instead of create new experiment
    with Run(
        experiment_name=exp_name,
        run_name=unique_name_from_base(exp_name + "-run"),
        sagemaker_session=session,
    ) as run:
        train(run)
