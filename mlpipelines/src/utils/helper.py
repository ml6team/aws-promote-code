"""General helper methods for Sagemaker Pipeline"""
import os
import pandas as pd
import numpy as np

import torch
from torch.utils.data import Dataset

from transformers import AutoTokenizer, AutoModelForSequenceClassification

import config



class MyTokenizer:
    def __init__(self, model_name=config.MODEL_NAME) -> None:
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

    def tokenize(self, txt_input):
        return self.tokenizer.encode(txt_input, padding="max_length", truncation=True)


class Encoder:
    def __init__(self, train_data, test_data) -> None:
        self.df = pd.concat([train_data, test_data])
        categories = self.df.medical_specialty.astype(
            "category").cat.categories
        self.cat_dict = {cat: i for i, cat in enumerate(categories)}
        self.val_dict = {i: cat for i, cat in enumerate(categories)}
        self.num_cat = np.array([len(self.cat_dict)])

    def encode(self, category: str) -> int:
        return self.cat_dict[category]

    def decode(self, code: int) -> str:
        return self.val_dict[code]


class MyDataset(Dataset):
    def __init__(self, x, y):
        self.x = torch.tensor(x)
        self.y = torch.tensor(y)

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        return self.x[idx], self.y[idx]


def load_dataset(dir, file_extension: str):
    allowed_extensions = ["train", "test"]
    if file_extension not in allowed_extensions:
        raise ValueError("Invalid extension. Expected one of: %s" % allowed_extensions)

    x_train = np.load(os.path.join(dir, f"x_{file_extension}.npy"))
    y_train = np.load(os.path.join(dir, f"y_{file_extension}.npy"))

    return MyDataset(x_train, y_train)

def load_num_labels(label_dir):
    return np.load(os.path.join(label_dir, 'num_labels.npy'))[0]


def get_model(num_labels):
    return AutoModelForSequenceClassification.from_pretrained(
        config.MODEL_NAME,
        num_labels=num_labels,
    )
    
