import os

import boto3
import mlflow


def download_directory(
        bucket_name,
        path,
        access_key,
        secret_key,
        endpoint_url):
    resource = boto3.resource(
        's3',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        endpoint_url=endpoint_url

    )

    bucket = resource.Bucket(bucket_name)

    for obj in bucket.objects.filter(Prefix=path):
        if not os.path.exists(os.path.dirname(obj.key)):
            os.makedirs(os.path.dirname(obj.key))
        key = obj.key
        print(f'Downloading {key}')
        bucket.download_file(key, key)


if __name__ == '__main__':
    path = '0/072084f402a942bf8dad8b4708502c08/artifacts'
    download_directory(bucket_name='mlflow', path=path, access_key='minioadmin', secret_key='minioadmin',
                       endpoint_url='http://39.105.6.98:43098')
    mlflow.projects.run(uri=path + '/model', env_manager='conda')
    mlflow.projects.SubmittedRun
    # project_uri = "https://github.com/mlflow/mlflow-example"
    # params = {"alpha": 0.5, "l1_ratio": 0.01}

    # Run MLflow project and create a reproducible conda environment
    # on a local host
    # mlflow.run(project_uri, parameters=params)