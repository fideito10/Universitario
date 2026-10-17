web: python scripts/write_auth_secrets.py && streamlit run main_universitario.py --server.port $PORT --server.address 0.0.0.0
worker: python -m src.data.sync --loop --every 300
