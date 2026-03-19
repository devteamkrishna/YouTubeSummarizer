FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# agar FastAPI hai
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8012"]

# agar Flask hai
# CMD ["python", "app.py"]

# agar Streamlit hai
# CMD ["streamlit", "run", "app.py", "--server.port=8012", "--server.address=0.0.0.0"]
