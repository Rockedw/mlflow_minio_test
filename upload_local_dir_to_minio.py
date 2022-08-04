import os

import boto3
import numpy as np
from sklearn.linear_model import LogisticRegression

import mlflow
import mlflow.sklearn

os.environ["AWS_ACCESS_KEY_ID"] = "minioadmin"
os.environ["AWS_SECRET_ACCESS_KEY"] = "minioadmin"
os.environ["MLFLOW_S3_ENDPOINT_URL"] = f"http://39.105.6.98:43098"


def transform(model_path):
    pass


if __name__ == "__main__":
    model_path = './upload_test'
    mlflow.tracking.set_tracking_uri('http://39.105.6.98:43100')
    mlflow.log_artifacts(local_dir=model_path, artifact_path='model')
    artifact_uri = mlflow.get_artifact_uri()
    print("Artifact uri: {}".format(artifact_uri))
    mv = mlflow.register_model(artifact_uri, "register_model_test")
    print("Name: {}".format(mv.name))
    print("Version: {}".format(mv.version))

    # upload(model_path)
