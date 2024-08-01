FROM python:3.9-slim

WORKDIR /app

COPY client_secret.json /app/client_secret.json
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]