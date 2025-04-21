import os
import requests
from requests import basic_auth
from dotenv import load_dotenv

load_dotenv()

api_user = os.getenv()
api_pw = os.getenv()

