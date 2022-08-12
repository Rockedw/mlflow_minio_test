import stat
import boto3
from flask import Flask, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import pymysql
import os
import subprocess
from git import Repo
from config import Config

from JsonResponse import JsonResponse

pymysql.install_as_MySQLdb()

app = Flask(__name__)
CORS(app, resources=r'/*')
db = SQLAlchemy(app)
# SQLALCHEMY_BINDS = {
#     'mlflow': 'mysql://root:wangyan123@39.105.6.98:43306/mlflow',
#     'gitea': 'mysql://root:wangyan123@39.105.6.98:43306/gitea'
# }
# SQLALCHEMY_TRACK_MODIFICATIONS = True
# SQLALCHEMY_COMMIT_TEARDOWN = True
#
# # app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:wangyan123@39.105.6.98:43306/gitea"
# app.config['SQLALCHEMY_BINDS'] = SQLALCHEMY_BINDS
# app.config['SQLALCHEMY_ECHO'] = True
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

app.config.from_object(Config)

bucket_name = 'models'
access_key = 'minioadmin'
secret_key = 'minioadmin'
endpoint_url = 'http://39.105.6.98:43099'  # minio server地址
git_url = 'http://39.105.6.98:43000'


@app.errorhandler(Exception)
def error_handler(e):
    """
    全局异常捕获，也相当于一个视图函数
    """
    print(str(e))
    return JsonResponse.error(msg=str(e)).to_dict()


def rmtree(top):
    """
    递归删除文件夹
    :param top:
    :return:
    """
    for root, dirs, files in os.walk(top, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            os.chmod(filename, stat.S_IWUSR)
            os.remove(filename)
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(top)


def download_directory(download_path, save_path='./'):
    """
    从S3中下载模型到本地
    :param download_path:
    :param save_path:
    :return:
    """
    # bucket_name = 'models'
    resource = boto3.resource(
        's3',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        endpoint_url=endpoint_url
    )
    bucket = resource.Bucket(bucket_name)
    for obj in bucket.objects.filter(Prefix=download_path):
        if not os.path.exists(os.path.dirname(save_path + obj.key)):
            os.makedirs(os.path.dirname(save_path + obj.key))
        key = obj.key
        print(f'Downloading {key}')
        print(save_path + key)
        bucket.download_file(Key=key, Filename=save_path + key)


def cmd(command):
    """
    执行bash或这cmd命令
    :param command:
    :return:
    """
    subp = None
    try:
        subp = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
        subp.wait()
        print(subp.communicate()[1])
    except Exception as e:
        print(str(e))

    if subp.poll() == 0:
        print(subp.communicate()[1])
    else:
        print("失败")


class Repository(db.Model):
    __tablename__ = 'repository'
    __bind_key__ = 'gitea'
    id = db.Column(db.Integer, primary_key=True, index=True)
    owner_id = db.Column('owner_id', db.Integer)
    owner_name = db.Column('owner_name', db.String(255))
    lower_name = db.Column('lower_name', db.String(255))
    repo_name = db.Column('name', db.String(255))


class Model(db.Model):
    __tablename__ = 'model_versions'
    __bind_key__ = 'mlflow'
    name = db.Column('name', db.String(256), primary_key=True)
    version = db.Column('version', db.Integer, primary_key=True)
    source = db.Column('source', db.String(500))


def query_repos():
    repos = Repository.query.all()
    res = []
    for repo in repos:
        res.append(
            {'id': repo.id, 'owner_name': repo.owner_name, 'repo_name': repo.repo_name, 'lower_name': repo.lower_name})
    return res


def query_branches_by_repo_name_and_owner(owner_name, repo_name):
    repo_url = git_url + '/' + owner_name + '/' + repo_name + '.git'
    print(repo_url)
    to_path = repo_name
    if os.path.exists(to_path):
        # repo = Repo(to_path)
        # remote = repo.remote()
        # remote.fetch()
        # 删除本地文件
        rmtree(to_path)
        # pass
    repo = Repo.clone_from(url=repo_url, to_path=to_path)
    remote_branches = []
    for ref in repo.git.branch('-r').split('\n'):
        print(ref)
        remote_branches.append(ref)
    print(remote_branches)
    # cwd = os.getcwd()
    # os.chdir(repo_name)
    # cmd('git checkout ' + remote_branches[2])
    # os.chdir(cwd)
    return remote_branches


@app.route('/')
def index():
    # repo = Repository(owner_name='wangyan', repo_name='hello world', lower_name='hello world')
    # db.session.add(repo)
    # return JsonResponse.success(data=str(query_repos())).to_dict()
    models = Model.query.all()
    temp = []
    for model in models:
        temp.append(model.name)
    return str(temp)


@app.route('/query_branches_by_owner_and_name', methods=['POST'])
def query_branches_by_owner_and_name():
    # return os.getcwd()
    data = request.json
    repo_name = data.get('repo_name')
    owner_name = data.get('owner_name')
    branches = query_branches_by_repo_name_and_owner(owner_name=owner_name,
                                                     repo_name=repo_name)
    return JsonResponse.success(data=branches).to_dict()


@app.route('/query_all_model', methods=['GET'])
def query_all_model():
    model_list = Model.query.all()
    models = {}
    for model in model_list:
        if model.name not in models:
            models[model.name] = [{'model_version': model.version, 'model_source': model.source}]
        else:
            model[model.name].append({'model_version': model.version, 'model_source': model.source})
    return JsonResponse.success(data=models).to_dict()


@app.route('/download_model_by_name_and_version', methods=['POST'])
def download_model_by_name_and_version():
    model_name = request.json.get('model_name')
    model_version = request.json.get('model_version')
    model = Model.query.filter_by(name=model_name, version=model_version).all()
    if len(model) <= 0:
        return JsonResponse.error().to_dict()
    model_source: str = model[0].source
    path = model_source.split('//' + bucket_name + '/')[1] + '/model'
    download_directory(download_path=path)

    return str(os.path.exists(path))


@app.route('/change_branch_by_branch_name', methods=['POST'])
def change_branch_by_name():
    data = request.json
    owner_name = data.get('owner_name')
    repo_name = data.get('repo_name')
    branch_name = data.get('branch_name')

    repo_url = git_url + '/' + owner_name + '/' + repo_name + '.git'
    print(repo_url)
    to_path = repo_name
    repo = None
    if not os.path.exists(to_path):
        # repo = Repo(to_path)
        # remote = repo.remote()
        # remote.fetch()
        # 删除本地文件
        # rmtree(to_path)
        return JsonResponse.error(msg='There is no git directory').to_dict()
    cwd = os.getcwd()
    command = 'cd ' + cwd + ' && ' + 'cd ' + repo_name + ' && ' + 'git checkout ' + branch_name
    print(command)
    cmd(command)
    return JsonResponse.success(data=os.getcwd()).to_dict()


@app.route('/run_mlflow_project_by_name_and_branch', methods=['POST'])
def run_mlflow_project():
    data = request.json
    owner_name = data.get('owner_name')
    repo_name = data.get('repo_name')
    branch_name = data.get('branch_name')

    repo_url = git_url + '/' + owner_name + '/' + repo_name + '.git'
    print(repo_url)
    to_path = repo_name
    repo = None
    if not os.path.exists(to_path):
        # repo = Repo(to_path)
        # remote = repo.remote()
        # remote.fetch()
        # 删除本地文件
        # rmtree(to_path)
        return JsonResponse.error(msg='There is no git directory').to_dict()
    cwd = os.getcwd()
    if not os.path.exists(to_path+'/.git'):
        print(to_path+'/.git 不存在')
        query_branches_by_repo_name_and_owner(repo_name=repo_name,owner_name=owner_name)
    command = 'cd ' + cwd + ' && ' + \
              'cd ' + repo_name + ' && ' + \
              'git checkout ' + branch_name + ' && ' + \
              'rm -rf .git &&' + \
              'cd ' + cwd + ' && ' + \
              'mlflow run ' + cwd + '/' + repo_name
    print(command)
    cmd(command)

    return JsonResponse.success(data=os.getcwd()).to_dict()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=False)
