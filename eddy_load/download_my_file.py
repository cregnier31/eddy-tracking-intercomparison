# ============================================================
#                     download_my_file.py
# ============================================================
#
# Descrition : Allows to download files from the S3 bucket 
#              "My File" of my EDITO account to my ongoing 
#              EDITO service local directory.
#
# Author     : S. Cailleau
# Version    : 11/09/2024
# ============================================================
#
import s3fs
import os
import glob
#
from namelist_my_file import *
#
#  Refresh S3 credentials in my ongoing service (updated every 24h) 
#
print("AWS_ACCESS_KEY_ID = ",os.environ["AWS_ACCESS_KEY_ID"])
print("AWS_SECRET_ACCESS_KEY = ",os.environ["AWS_SECRET_ACCESS_KEY"])
print("AWS_SESSION_TOKEN = ",os.environ["AWS_SESSION_TOKEN"])
#
os.environ["AWS_DEFAULT_REGION"] = 'waw3-1'
fs = s3fs.S3FileSystem(
    client_kwargs={'endpoint_url': 'https://'+'minio.dive.edito.eu'},
    key = os.environ["AWS_ACCESS_KEY_ID"], 
    secret = os.environ["AWS_SECRET_ACCESS_KEY"], 
    token = os.environ["AWS_SESSION_TOKEN"])
#                           
#  Downloading from S3 My File
#
file_list = fs.ls(my_file_dir)
for file in file_list:
   fs.download(file, local_dir)
#                           
# ============================================================
#