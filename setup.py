# coding:utf-8
# @author: ssh
from setuptools import setup, find_packages

NAME = 'okex'

VERSION = '0.0.1'

REQUIRES = [
    'openpyxl>=3.0.9',
    'pandas>=2.0.0',
    'numpy>=1.24.2',
    'matplotlib>=3.7.1',
    "websockets>=12.0"
]

setup(
    name=NAME,  # 包名字
    version=VERSION,  # 包版本
    author='ssh',  # 作者
    author_email='ssh21927@gmail.com',  # 作者邮箱
    url='https://github.com/SSH-C12138/okex.git',  # 包的主页
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={'': ['*.json']},
)
