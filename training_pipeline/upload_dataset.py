"""Split local dataset (csv) in train an test. Then upload to Sagemaker S3 bucket."""
from io import StringIO
import numpy as np
import pandas as pd
import boto3
import sagemaker

sagemaker_session = sagemaker.session.Session()


def upload_df(df, file_name):
    """Upload Pandas Dataframe to Sagemaker default bucket"""
    default_bucket = sagemaker_session.default_bucket()
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    s3_resource = boto3.resource("s3")
    s3_resource.Object(default_bucket, f"data/{file_name}").put(
        Body=csv_buffer.getvalue()
    )


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
upload_df(train, "train.csv")
upload_df(test, "test.csv")
upload_df(val, "val.csv")
