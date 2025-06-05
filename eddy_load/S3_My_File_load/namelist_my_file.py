import os
#
# Local directory of my ongoing EDITO service
# -------------------------------------------
local_dir = "/home/jovyan/work/DATA/AVISO/"
#
# S3 bucket My File distant directory of my EDITO account
# -------------------------------------------------------
my_file_dir = "s3://oidc-scailleau/DATA/GLO/"
#
# Refresh S3 credentials in the service
# -------------------------------------
# to copy every 24h from : https://datalab.dive.edito.eu/account/storage (from the Python s3fs snippet)
os.environ["AWS_ACCESS_KEY_ID"] = 'Z9HAA5EORCN8U1STN0AH'
os.environ["AWS_SECRET_ACCESS_KEY"] ='XYODkNKfz0j2kvhBjWLTt9W4ZBzEeqjqVAcfaJUE'
os.environ["AWS_SESSION_TOKEN"] = 'eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3NLZXkiOiJaOUhBQTVFT1JDTjhVMVNUTjBBSCIsImFjciI6IjAiLCJhbGxvd2VkLW9yaWdpbnMiOlsiKiJdLCJhdWQiOlsibWluaW8iLCJhY2NvdW50Il0sImF1dGhfdGltZSI6MTc0ODkzODkyMywiYXpwIjoib255eGlhLW1pbmlvIiwiZW1haWwiOiJzY2FpbGxlYXVAbWVyY2F0b3Itb2NlYW4uZnIiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZXhwIjoxNzQ5MDI4NDYzLCJmYW1pbHlfbmFtZSI6IkNBSUxMRUFVIiwiZ2l2ZW5fbmFtZSI6IlNZTFZBSU4iLCJncm91cHMiOlsiRURJVE9fVVNFUiIsInZhbGlkYXRpb24tbW9pIl0sImlhdCI6MTc0ODk0MjA2MywiaXNzIjoiaHR0cHM6Ly9hdXRoLmRpdmUuZWRpdG8uZXUvYXV0aC9yZWFsbXMvZGF0YWxhYiIsImp0aSI6IjY3MTY3ZTEyLTdjMmItNDI3ZC04MmZiLTI3YTJhNzdjOTVhZiIsIm5hbWUiOiJTWUxWQUlOIENBSUxMRUFVIiwicG9saWN5Ijoic3Rzb25seSIsInByZWZlcnJlZF91c2VybmFtZSI6InNjYWlsbGVhdSIsInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJkZWZhdWx0LXJvbGVzLWRhdGFsYWIiLCJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19LCJtaW5pbyI6eyJyb2xlcyI6WyJzdHNvbmx5Il19fSwic2NvcGUiOiJvcGVuaWQgZW1haWwgcHJvZmlsZSIsInNlc3Npb25fc3RhdGUiOiIxYTg0NWIzYy1kNTkyLTRiMmUtYjFjNC1kYTYxOGU5ZTc1MTAiLCJzaWQiOiIxYTg0NWIzYy1kNTkyLTRiMmUtYjFjNC1kYTYxOGU5ZTc1MTAiLCJzdWIiOiI0NzdiYTdkNS0yZmYzLTQ1NTktOTlkZS0xMDUyZjZjY2VjNjMiLCJ0eXAiOiJCZWFyZXIifQ.efIP-UZsiO_soi3SKNdCyzepnQt3HTuv-sc-UeS7tGbVXZRBMtN-buKIRA_AxHkhh2mhoZlbVGR5eTlBvxnWdw'
#
# ============================================================
