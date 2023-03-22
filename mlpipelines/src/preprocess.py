import numpy as np
import pandas as pd
import os
import logging

from utils.helper import MyTokenizer, Encoder

def preprocess():
    logging.warning('fetching dataset')
    df_train = pd.read_csv(os.path.join(
        "/opt/ml/processing/input/train", "train.csv"))
    df_test = pd.read_csv(os.path.join(
        "/opt/ml/processing/input/test", "test.csv"))

    logging.warning('tokenizing dataset')
    tokenizer = MyTokenizer()
    x_train = [tokenizer.tokenize(v) for v in df_train.transcription.values]
    x_test = [tokenizer.tokenize(v) for v in df_test.transcription.values]
    encoder = Encoder(df_train, df_test)
    y_train = [encoder.encode(c) for c in df_train.medical_specialty.values]
    y_test = [encoder.encode(c) for c in df_test.medical_specialty.values]

    logging.warning('saving dataset')

    # save data
    np.save(os.path.join("/opt/ml/processing/output/train", "x_train.npy"), x_train)
    np.save(os.path.join("/opt/ml/processing/output/train", "y_train.npy"), y_train)
    np.save(os.path.join("/opt/ml/processing/output/test", "x_test.npy"), x_test)
    np.save(os.path.join("/opt/ml/processing/output/test", "y_test.npy"), y_test)
    
    # TODO save as (huggingface) dataset
    
    # save num_of_labels
    np.save(os.path.join("/opt/ml/processing/output/labels", "num_labels.npy"), encoder.num_cat)


if __name__ == "__main__":
    preprocess()
