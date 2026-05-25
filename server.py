import os
import subprocess

port = os.environ.get("PORT", "8501")

cmd = f"streamlit run app.py --server.port {port} --server.address 0.0.0.0"

subprocess.call(cmd, shell=True)