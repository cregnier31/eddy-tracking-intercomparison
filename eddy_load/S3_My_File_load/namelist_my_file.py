import os
#
# Local directory of my ongoing EDITO service
# -------------------------------------------
local_dir = "/home/jovyan/data/AVISO_EU/"
#
# S3 bucket My File distant directory of my EDITO account
# -------------------------------------------------------
my_file_dir = "s3://oidc-scailleau/DATA/AVISO/"
#
# Refresh S3 credentials in the service
# -------------------------------------
# to copy every 24h from : https://datalab.dive.edito.eu/account/storage (from the Python s3fs snippet)
os.environ["AWS_ACCESS_KEY_ID"] = 'Y5Y0O4U3B2HECJRH8I1V'
os.environ["AWS_SECRET_ACCESS_KEY"]  = 'rsrL9VV3q0f+gW6OMG1O83FVRPR7G0l1NphNd+Zw'
os.environ["AWS_SESSION_TOKEN"] = 'eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3NLZXkiOiJZNVkwTzRVM0IySEVDSlJIOEkxViIsImFjciI6IjAiLCJhbGxvd2VkLW9yaWdpbnMiOlsiKiJdLCJhdWQiOlsibWluaW8iLCJhY2NvdW50Il0sImF1dGhfdGltZSI6MTc1NjI5MjU5OCwiYXpwIjoib255eGlhLW1pbmlvIiwiZW1haWwiOiJzY2FpbGxlYXVAbWVyY2F0b3Itb2NlYW4uZnIiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZXhwIjoxNzU2Mzk1MTQxLCJmYW1pbHlfbmFtZSI6IkNBSUxMRUFVIiwiZ2l2ZW5fbmFtZSI6IlNZTFZBSU4iLCJncm91cHMiOlsiRURJVE9fVVNFUiIsInZhbGlkYXRpb24tbW9pIl0sImlhdCI6MTc1NjMwODc0MSwiaXNzIjoiaHR0cHM6Ly9hdXRoLmRpdmUuZWRpdG8uZXUvYXV0aC9yZWFsbXMvZGF0YWxhYiIsImp0aSI6IjNmOGVmYzMzLTcwMzctNDFiNy1hZmNiLTU5YzIwMDFhMTE0OCIsIm5hbWUiOiJTWUxWQUlOIENBSUxMRUFVIiwicG9saWN5Ijoic3Rzb25seSIsInByZWZlcnJlZF91c2VybmFtZSI6InNjYWlsbGVhdSIsInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJkZWZhdWx0LXJvbGVzLWRhdGFsYWIiLCJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19LCJtaW5pbyI6eyJyb2xlcyI6WyJzdHNvbmx5Il19fSwic2NvcGUiOiJvcGVuaWQgZW1haWwgcHJvZmlsZSIsInNlc3Npb25fc3RhdGUiOiI2MTFjY2VjYS0xZTViLTRiYTItYmUyOC1iOTRlMjZmMGE3NTIiLCJzaWQiOiI2MTFjY2VjYS0xZTViLTRiYTItYmUyOC1iOTRlMjZmMGE3NTIiLCJzdWIiOiI0NzdiYTdkNS0yZmYzLTQ1NTktOTlkZS0xMDUyZjZjY2VjNjMiLCJ0eXAiOiJCZWFyZXIifQ.AV_uDcCJTTdN7k1JxtF1OdWfecci5GEfyJMiLeognh4SHgUBwJHSOKrttM6BHXPYqM_lpptdipjx7imOs6bLYw'
#
# ============================================================
