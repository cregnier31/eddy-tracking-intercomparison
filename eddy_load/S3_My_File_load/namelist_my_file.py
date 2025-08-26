import os
#
# Local directory of my ongoing EDITO service
# -------------------------------------------
local_dir = "/home/jovyan/data/ORCA36/PLOTS"
#
# S3 bucket My File distant directory of my EDITO account
# -------------------------------------------------------
my_file_dir = "s3://oidc-scailleau/DATA/ORCA36/"
#
# Refresh S3 credentials in the service
# -------------------------------------
# to copy every 24h from : https://datalab.dive.edito.eu/account/storage (from the Python s3fs snippet)
os.environ["AWS_ACCESS_KEY_ID"] = '57539N8LR6KGOAE1JKJK'
os.environ["AWS_SECRET_ACCESS_KEY"]  = 'zB5mxZyP3YNPlJcll3l+77hde1sQA+ITlcbzUsjm'
os.environ["AWS_SESSION_TOKEN"] = 'eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3NLZXkiOiI1NzUzOU44TFI2S0dPQUUxSktKSyIsImFjciI6IjAiLCJhbGxvd2VkLW9yaWdpbnMiOlsiKiJdLCJhdWQiOlsibWluaW8iLCJhY2NvdW50Il0sImF1dGhfdGltZSI6MTc1NjE5NzA5NSwiYXpwIjoib255eGlhLW1pbmlvIiwiZW1haWwiOiJzY2FpbGxlYXVAbWVyY2F0b3Itb2NlYW4uZnIiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiZXhwIjoxNzU2MjgzNTE1LCJmYW1pbHlfbmFtZSI6IkNBSUxMRUFVIiwiZ2l2ZW5fbmFtZSI6IlNZTFZBSU4iLCJncm91cHMiOlsiRURJVE9fVVNFUiIsInZhbGlkYXRpb24tbW9pIl0sImlhdCI6MTc1NjE5NzExNSwiaXNzIjoiaHR0cHM6Ly9hdXRoLmRpdmUuZWRpdG8uZXUvYXV0aC9yZWFsbXMvZGF0YWxhYiIsImp0aSI6IjZiMTJlYjM5LWQ3M2ItNDhiNi04M2NhLWI0ZTA4NmIzZGIyNCIsIm5hbWUiOiJTWUxWQUlOIENBSUxMRUFVIiwicG9saWN5Ijoic3Rzb25seSIsInByZWZlcnJlZF91c2VybmFtZSI6InNjYWlsbGVhdSIsInJlYWxtX2FjY2VzcyI6eyJyb2xlcyI6WyJkZWZhdWx0LXJvbGVzLWRhdGFsYWIiLCJvZmZsaW5lX2FjY2VzcyIsInVtYV9hdXRob3JpemF0aW9uIl19LCJyZXNvdXJjZV9hY2Nlc3MiOnsiYWNjb3VudCI6eyJyb2xlcyI6WyJtYW5hZ2UtYWNjb3VudCIsIm1hbmFnZS1hY2NvdW50LWxpbmtzIiwidmlldy1wcm9maWxlIl19LCJtaW5pbyI6eyJyb2xlcyI6WyJzdHNvbmx5Il19fSwic2NvcGUiOiJvcGVuaWQgZW1haWwgcHJvZmlsZSIsInNlc3Npb25fc3RhdGUiOiJlOWM2ZTk0Ni00ZDdhLTRiN2ItODgwNi0yYzNjYjk0YWY2M2YiLCJzaWQiOiJlOWM2ZTk0Ni00ZDdhLTRiN2ItODgwNi0yYzNjYjk0YWY2M2YiLCJzdWIiOiI0NzdiYTdkNS0yZmYzLTQ1NTktOTlkZS0xMDUyZjZjY2VjNjMiLCJ0eXAiOiJCZWFyZXIifQ.Wxsla_0Lj2OzAcMPtxY4vWgEWlM3qAtsCqEYgUsk2_kTYzMQYtQLdty2u7ePbE_Mkw8rxqbhUfHj69rXNmOVXQ'
#
# ============================================================
