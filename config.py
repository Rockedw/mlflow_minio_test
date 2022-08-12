class Config:
    SQLALCHEMY_BINDS = {
        'mlflow': 'mysql://root:wangyan123@39.105.6.98:43306/mlflow',
        'gitea': 'mysql://root:wangyan123@39.105.6.98:43306/gitea'
    }
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_COMMIT_TEARDOWN = True
    SQLALCHEMY_ECHO = True
