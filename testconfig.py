# -*-coding:utf8-*-
from localconfig import *
import os

DEBUG = True
TESTING = True

DYNAMODB_PORT = 8001
TESTING_PATH = os.path.split(os.path.abspath(__file__))[0]
