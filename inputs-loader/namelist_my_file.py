import os
#
# Local directory of my ongoing EDITO service
# -------------------------------------------
local_dir = "/home/jovyan/work/DATA/AVISO/"
#
# S3 bucket My File distant directory of my EDITO account
# -------------------------------------------------------
my_file_dir = "s3://oidc-scailleau/DATA/AVISO/"
#
# Refresh S3 credentials in the service
# -------------------------------------
# to copy every 24h from : https://datalab.dive.edito.eu/account/storage (from the Python s3fs snippet)
os.environ["AWS_ACCESS_KEY_ID"] = 'AXTQCHQY470M42X8BU4C'
os.environ["AWS_SECRET_ACCESS_KEY"] = 'DXRp4KezEwtKgFzhRJds3QdQ4wLhuNA3xbd0HYZf'
os.environ["AWS_SESSION_TOKEN"] = 'eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3NLZXkiOiJBWFRRQ0hRWTQ3ME00Mlg4QlU0QyIsImFjciI6IjAiLCJhbGxvd2VkLW9yaWdpbnMiOlsiKiJdLCJhdWQiOlsibWluaW8iLCJhY2NvdW50Il0sImF1dGhfdGltZSI6MTc0MTYwNTIzNCwiYXpwIjoib255eGlhLW1pbmlvIiwiZW1haWwiOiJzY2FpbGxlYXVAbWVyY2F0b3Itb2NlYW4uZnIiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZXhwIjoxNzQxNzAyNjU4LCJmYW1pbHlfbmFtZSI6IkNBSUxMRUFVIiwiZ2l2ZW5fbmFtZSI6IlNZTFZBSU4iLCJncm91cHMiOlsiRURJVE9fVVNFUiIsInZhbGlkYXRpb24tbW9pIl0sImlhdCI6MTc0MTYxNjI1OCwiaXNzIjoiaHR0cHM6Ly9hdXRoLmRpdmUuZWRpdG8uZXUvYXV0aC9yZWFsbXMvZGF0YWxhYiIsImp0aSI6IjdiNjBiZmQ0LTE1OGQtNGY3Ny1iODUzLTI1YTU2NGNmNDE4YyIsIm5hbWUiOiJTWUxWQUlOIENBSUxMRUFVIiwicG9saWN5Ijoic3Rzb25seSIsInByZWZlcnJlZF91c2VybmFtZSI6InNjYWlsbGVhdSIsInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJkZWZhdWx0LXJvbGVzLWRhdGFsYWIiLCJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19LCJtaW5pbyI6eyJyb2xlcyI6WyJzdHNvbmx5Il19fSwic2NvcGUiOiJvcGVuaWQgZW1haWwgcHJvZmlsZSIsInNlc3Npb25fc3RhdGUiOiI4YmMxMjQ3OC02ODQ2LTRhNjEtOGVjYS02ZGI5Yzg2NTUzZmYiLCJzaWQiOiI4YmMxMjQ3OC02ODQ2LTRhNjEtOGVjYS02ZGI5Yzg2NTUzZmYiLCJzdWIiOiI0NzdiYTdkNS0yZmYzLTQ1NTktOTlkZS0xMDUyZjZjY2VjNjMiLCJ0eXAiOiJCZWFyZXIifQ.OERSPIXiBAmKrLKD51dzuSy9gVMmSIjRMaJ_CvzTHsPdu0ikdSNHbTPxmI1gKqNCb38K5o6mP38C1zU8r6M_aA'A'O4pA'
#
# ============================================================