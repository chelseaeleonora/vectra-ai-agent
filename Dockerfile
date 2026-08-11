FROM python:3.12-slim

WORKDIR /app

# Install dependencies dengan versi proven
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy seluruh kode
COPY . .

EXPOSE 8000

CMD ["chainlit", "run", "backend/chainlit_app.py", "--host", "0.0.0.0", "--port", "8000", "--headless"]