import stat
import boto3
import os
import subprocess

bucket_name = 'models'
access_key = 'minioadmin'
secret_key = 'minioadmin'
endpoint_url = 'http://39.105.6.98:43099'  # minio server地址
git_url = 'http://39.105.6.98:43000'  # gitea地址

from JsonResponse import JsonResponse


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


class Node:
    def __init__(self, name, path, is_dir=False):
        if is_dir:
            self.children = []
        else:
            self.children = None
        self.name = name
        self.path = path

    def append_child(self, child):
        self.children.append(child)


# def scan_dir(path, head: Node):
#     for name in os.listdir(path):
#         if os.path.isdir(path + os.sep + name):
#             node = Node(is_dir=True, path=path + os.sep + name, name=name)
#             head.append_child(node)
#             scan_dir(path + os.sep + name, node)
#         else:
#             node = Node(is_dir=False, path=path + os.sep + name, name=name)
#             head.append_child(node)


def scan_dir(path, head: dict = None):
    if os.path.isdir(path):
        if head is None:
            head = {'is_dir': True, 'title': os.path.basename(path), 'key': path, 'children': []}
    else:
        return {'is_dir': False, 'title': os.path.basename(path), 'key': path, }
    for name in os.listdir(path):
        if name == '.git':
            pass
        elif os.path.isdir(path + os.sep + name):
            temp = {'is_dir': True, 'title': name, 'key': path + os.sep + name, 'children': []}
            scan_dir(path + os.sep + name, temp)
            head['children'].append(temp)
        else:
            temp = {'is_dir': False, 'title': name, 'key': path + os.sep + name}
            head['children'].append(temp)
    return head


if __name__ == '__main__':
    path = r'C:\Users\wangyan\PycharmProjects\MLFlow\repos'
    head = scan_dir(path)
    print(str(head))
