# ============================================================
#                     upload_my_file.py
# ============================================================
#
# Descrition : Allows to upload files from a local directory
#              of my ongoing EDITO service to the S3 bucket 
#              "My File" of my EDITO account
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
#  Uploading to S3 My File
#
for file in glob.glob( os.path.join(local_dir, 'AVISO_EU_20200101.nc') ):
   fs.upload(file, my_file_dir)
#                           
# ============================================================
#