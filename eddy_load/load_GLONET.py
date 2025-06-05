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
# ------
# IMPORT
# ------
#
import s3fs
import os
import glob
import boto3
import xarray as xr
import numpy as np
from typing import List
#
# Local directory of my ongoing EDITO service
# -------------------------------------------
#local_dir = "/home/jovyan/work/DATA/AVISO/"
#
# S3 bucket My File distant directory of my EDITO account
# -------------------------------------------------------
#my_file_dir = "s3://oidc-scailleau/DATA/GLO/"
#
# ---------
# FUNCTIONS
# ---------
#
# Get S3 access of my EDITO account (S3 credentials in my ongoing service is refreshed every 24h)
def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=os.environ["S3_ENDPOINT"],
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        aws_session_token=os.environ["AWS_SESSION_TOKEN"],
    )
#
# Uppload bytes (data files) to EDITO S3 bucket
def save_bytes_to_s3(bucket_name: str, object_bytes, object_key: str):
    response = get_s3_client().put_object(
        Bucket=bucket_name,
        Body=object_bytes,
        Key=object_key,
    )
    if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
        print(f"Successfully uploaded bytes to S3 {bucket_name}/{object_key}")
    else:
        print(f"Failed to upload bytes to S3 {bucket_name}/{object_key}: {response}")
#
#s3 = s3fs.S3FileSystem(client_kwargs={'endpoint_url': 'https://minio.dive.edito.eu'}, anon=True)
#remote_dataset = s3.open('oidc-scailleau/DATA/AVISO/AVISO_20250207.nc')
#dataset = xarray.open_dataset(remote_dataset)
#ssu_obs = dataset.variables['ugos'].values
#print (ssu_obs)


# Open GLONET forecast sample with xarray
date_glonet = "2024-01-03"
zmin = 0.
zmax = 0.5
#    - IBI
xmin=-19.
xmax=5.
ymin=26.
ymax=56.

dataset = (xr.open_dataset("https://minio.dive.edito.eu/project-oceanbench/public/glonet_full_2024/20240103.zarr", engine="zarr")).sel(time=slice(date_glonet,date_glonet), depth=slice(zmin,zmax), lon=slice(xmin,xmax), lat=slice(ymin,ymax))
ssu_mod = dataset['uo'].values
#                           
# ============================================================
#
