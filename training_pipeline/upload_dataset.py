"""Split local dataset (csv) in train an test. Then upload to Sagemaker S3 bucket."""
import argparse
from io import StringIO
import numpy as np
import pandas as pd

import boto3
import sagemaker


def upload_df(df, file_name, bucket_name):
    """Uploads Pandas Dataframe as csv to Sagemaker bucket"""

    if bucket_name == "sagemaker_default":
        sagemaker_session = sagemaker.session.Session()
        bucket_name = sagemaker_session.default_bucket()

    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    s3_resource = boto3.resource("s3")
    s3_resource.Object(bucket_name, f"data/{file_name}").put(Body=csv_buffer.getvalue())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--account", type=str, default="101436505502")
    parser.add_argument("--region", type=str, default="eu-west-3")
    parser.add_argument("--bucket-name", type=str, default="sagemaker_default")
    args = parser.parse_args()

    # load local dataset
    df = pd.read_csv("data/mtsamples.csv")

    # drop empty rows
    df = df[df["transcription"].notna()]

    # shuffle dataset
    df = df.sample(frac=1, random_state=42)

    # split the dataset into 70% train, 15% test and 15% validation
    train, test, val = np.split(df, [int(0.7 * len(df)), int(0.85 * len(df))])

    # reset indices
    train.reset_index(drop=True, inplace=True)
    test.reset_index(drop=True, inplace=True)
    val.reset_index(drop=True, inplace=True)

    # save data to S3
    upload_df(train, "train.csv", args.bucket_name)
    upload_df(test, "test.csv", args.bucket_name)
    upload_df(val, "val.csv", args.bucket_name)
