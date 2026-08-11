FROM python:3.12-slim

WORKDIR /app

# Install dependencies dengan versi proven
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh kode
COPY . .

EXPOSE 8000

CMD ["sh", "-c", "echo '=== VECTRA DEBUG DOCKERFILE ==='; echo PORT=$PORT; echo CHAINLIT_PORT=$CHAINLIT_PORT; echo '=== STARTING CHAINLIT ON 8000 ==='; env CHAINLIT_PORT=8000 chainlit run backend/chainlit_app.py --host 0.0.0.0 --port 8000 --headless"]
