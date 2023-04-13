"""Split local dataset (csv) in train an test. Then upload to Sagemaker S3 bucket."""
from io import StringIO
import pandas as pd
import boto3
import sagemaker

sagemaker_session = sagemaker.session.Session()

def upload_df(df, file_name):
    """Upload Pandas Dataframe to Sagemaker default bucket"""
    default_bucket = sagemaker_session.default_bucket()
    csv_buffer = StringIO()
    df.to_csv(csv_buffer)
    s3_resource = boto3.resource('s3')
    s3_resource.Object(default_bucket, f'data/{file_name}').put(Body=csv_buffer.getvalue())

# load local dataset
df = pd.read_csv("data/mtsamples.csv")

# drop empty rows
df = df[df["transcription"].notna()]

# split into train and test
train=df.sample(frac=0.8,random_state=42)
test=df.drop(train.index)

train.reset_index(drop=True, inplace=True)
test.reset_index(drop=True, inplace=True)

# save data to S3
upload_df(train, "train.csv")
upload_df(test, "test.csv")

