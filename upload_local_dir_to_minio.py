import os
import mlflow.sklearn

os.environ["AWS_ACCESS_KEY_ID"] = "minioadmin"
os.environ["AWS_SECRET_ACCESS_KEY"] = "minioadmin"
os.environ["MLFLOW_S3_ENDPOINT_URL"] = f"http://39.105.6.98:43099"


def transform(model_path):
    pass


if __name__ == "__main__":
    model_path = r'C:\Users\wangyan\PycharmProjects\MLFlow\0\0d47d35713ef483ebd245be79c516719\artifacts\model'
    mlflow.tracking.set_tracking_uri('http://39.105.6.98:43100')
    mlflow.log_artifacts(local_dir=model_path, artifact_path='model')
    artifact_uri = mlflow.get_artifact_uri()
    print("Artifact uri: {}".format(artifact_uri))
    mv = mlflow.register_model(artifact_uri, "model1")
    print("Name: {}".format(mv.name))
    print("Version: {}".format(mv.version))

    # upload(model_path)
