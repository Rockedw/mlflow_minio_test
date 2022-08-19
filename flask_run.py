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
from util_methods import cmd, download_directory, rmtree, scan_dir
import shutil

from JsonResponse import JsonResponse

pymysql.install_as_MySQLdb()

app = Flask(__name__)
CORS(app, resources=r'/*')
db = SQLAlchemy(app)

app.config.from_object(Config)

bucket_name = 'models'
access_key = 'minioadmin'
secret_key = 'minioadmin'
endpoint_url = 'http://39.105.6.98:43099'  # minio server地址
git_url = 'http://39.105.6.98:43000'  # gitea地址


class Repository(db.Model):
    __tablename__ = 'repository'
    __bind_key__ = 'gitea'
    id = db.Column(db.Integer, primary_key=True, index=True)
    owner_id = db.Column('owner_id', db.Integer)
    owner_name = db.Column('owner_name', db.String(255))
    lower_name = db.Column('lower_name', db.String(255))
    repo_name = db.Column('name', db.String(255))
    update_time = db.Column('updated_unix', db.Integer)


class Model(db.Model):
    __tablename__ = 'model_versions'
    __bind_key__ = 'mlflow'
    name = db.Column('name', db.String(256), primary_key=True)
    version = db.Column('version', db.Integer, primary_key=True)
    source = db.Column('source', db.String(500))


class Task(db.Model):
    __tablename__ = 'task'
    __bind_key__ = 'gitea'
    id = db.Column(db.Integer, primary_key=True, index=True)
    value = db.Column('value', db.String(255))


class TaskRelation(db.Model):
    __tablename__ = 'task_relation'
    __bind_key__ = 'gitea'
    id = db.Column(db.Integer, primary_key=True, index=True)
    task_id = db.Column(db.Integer)
    repo_id = db.Column(db.Integer)


# @app.errorhandler(Exception)
# def error_handler(e):
#     """
#     全局异常捕获，也相当于一个视图函数
#     """
#     print(str(e))
#     return JsonResponse.error(msg=str(e)).to_dict()


@app.route('/query_all_task', methods=['GET'])
def query_all_task():
    print('query all task')
    tasks = Task.query.all()
    res = []
    for task in tasks:
        res.append({'id': task.id, 'value': task.value})
    return JsonResponse.success(data=res).to_dict()


@app.route('/query_repo_by_task_id', methods=['POST'])
def query_repo_by_task_id():
    task_id = request.json.get('task_id')
    res = []
    task_relations = TaskRelation.query.filter_by(task_id=task_id).all()
    for task_relation in task_relations:
        temp = Repository.query.filter_by(id=task_relation.repo_id).all()
        if len(temp) > 0:
            res.append({'id': temp[0].id, 'owner_name': temp[0].owner_name, 'repo_name': temp[0].repo_name})
    print(res)
    return JsonResponse.success(data=res).to_dict()


def query_branches_by_repo_name_and_owner(owner_name, repo_name, update_time):
    repo_url = git_url + '/' + owner_name + '/' + repo_name + '.git'
    print(repo_url)
    path = './repos/' + owner_name + '/' + repo_name
    repo = None
    time = path + '/' + str(update_time) + '.time'
    if os.path.exists(path):
        if not os.path.exists(time):
            # repo = Repo(to_path)
            # remote = repo.remote()
            # remote.fetch()
            # 删除本地文件
            rmtree(path)
            repo = Repo.clone_from(url=repo_url, to_path=path)
            with open(time, 'a') as f:
                f.write('something')
            f.close()
        else:
            repo = Repo(path)
    else:
        repo = Repo.clone_from(url=repo_url, to_path=path)
        with open(time, 'a') as f:
            f.write('something')
        f.close()
    remote_branches = []
    for ref in repo.git.branch('-r').split('\n'):
        print(ref)
        remote_branches.append(ref)

    print(remote_branches)
    temp_path = './temp/repos/' + owner_name + '/' + repo_name
    try:
        temp_version = str(len(os.listdir(temp_path)))
    except Exception as e:
        temp_version = '0'

    to_path = temp_path + '/' + temp_version + '/' + repo_name
    shutil.copytree(path, to_path)

    return remote_branches, temp_version


@app.route('/query_all_repo')
def query_all_repo():
    # repo = Repository(owner_name='wangyan', repo_name='hello world', lower_name='hello world')
    # db.session.add(repo)
    repos = Repository.query.all()
    res = []
    for repo in repos:
        res.append(
            {'id': repo.id, 'owner_name': repo.owner_name, 'repo_name': repo.repo_name, 'lower_name': repo.lower_name,
             'update_time': repo.update_time})
    return JsonResponse.success(data=res).to_dict()


@app.route('/query_branches_by_owner_and_name', methods=['POST'])
def query_branches_by_owner_and_name():
    print('query_branches_by_owner_and_name excute')
    # return os.getcwd()
    data = request.json
    repo_name = data.get('repo_name')
    owner_name = data.get('owner_name')
    update_time = data.get('update_time')
    branches, temp_version = query_branches_by_repo_name_and_owner(owner_name=owner_name,
                                                                   repo_name=repo_name,
                                                                   update_time=update_time
                                                                   )
    print('branches : ' + str(branches))
    print('temp_version : ' + temp_version)
    if len(branches) > 0:
        return JsonResponse.success(data={'branches': branches, 'temp_version': temp_version}).to_dict()
    else:
        return JsonResponse.error().to_dict()


@app.route('/query_file_by_owner_and_name_and_branch', methods=['POST'])
def query_file_by_owner_and_name_and_branch():
    data_json = request.json
    owner_name = data_json.get('owner_name')
    repo_name = data_json.get('repo_name')
    branch_name = data_json.get('branch_name')
    temp_version = data_json.get('temp_version')
    print('abcded' + str(len(temp_version)))
    if len(temp_version) > 0:
        path = './temp/repos/' + owner_name + '/' + repo_name + '/' + temp_version + '/' + repo_name
    else:
        path = './repos/' + owner_name + '/' + repo_name
    print('*************************************************')
    print(path)
    print('*************************************************')
    if branch_name is not None:
        if not os.path.exists(path):
            return JsonResponse.error(msg='There is no git directory').to_dict()
        cwd = os.getcwd()
        command = 'cd ' + cwd + ' && ' + 'cd ' + path + ' && ' + 'git checkout ' + branch_name
        print(command)
        cmd(command)
    files = scan_dir(path)
    return JsonResponse.success(data=[files]).to_dict()


@app.route('/query_all_model', methods=['GET'])
def query_all_model():
    model_list = Model.query.all()
    models = {}
    res = []
    for model in model_list:
        if model.name not in models:
            models[model.name] = [{'model_version': model.version, 'model_source': model.source}]
        else:
            model[model.name].append({'model_version': model.version, 'model_source': model.source})
    # for key, value in models.items():
    #     res.append({key: value})
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
    temp_version = data.get('temp_version')
    path = './temp/repos/' + owner_name + '/' + repo_name + '/' + temp_version
    if not os.path.exists(path):
        return JsonResponse.error(msg='There is no git directory').to_dict()
    cwd = os.getcwd()
    command = 'cd ' + cwd + ' && ' + 'cd ' + path + ' && ' + 'git checkout ' + branch_name
    print(command)
    cmd(command)
    return JsonResponse.success(data=os.getcwd()).to_dict()


@app.route('/run_mlflow_project_by_name_and_branch', methods=['POST'])
def run_mlflow_project():
    data = request.json
    owner_name = data.get('owner_name')
    repo_name = data.get('repo_name')
    branch_name = data.get('branch_name')
    update_time = data.get('update_time')

    to_path = './repos/' + owner_name + repo_name
    repo = None
    if not os.path.exists(to_path):
        # repo = Repo(to_path)
        # remote = repo.remote()
        # remote.fetch()
        # 删除本地文件
        # rmtree(to_path)
        return JsonResponse.error(msg='There is no git directory').to_dict()
    cwd = os.getcwd()
    if not os.path.exists(to_path + '/.git'):
        print(to_path + '/.git 不存在')
        query_branches_by_repo_name_and_owner(repo_name=repo_name, owner_name=owner_name, update_time=update_time)
    command = 'cd ' + cwd + ' && ' + \
              'cd ' + repo_name + ' && ' + \
              'git checkout ' + branch_name + ' && ' + \
              'rm -rf .git &&' + \
              'cd ' + cwd + ' && ' + \
              'mlflow run ' + cwd + '/' + repo_name
    print(command)
    cmd(command)

    return JsonResponse.success(data=os.getcwd()).to_dict()


@app.route('/test', methods=['POST'])
def test():
    print(request.json)
    return JsonResponse.success().to_dict()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=True)
