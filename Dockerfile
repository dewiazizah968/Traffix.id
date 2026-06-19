FROM python:3.12-slim

WORKDIR /app

# Copy seluruh repo
COPY . .

# Install dependencies dari folder backend
WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt

# Start server
CMD uvicorn app.main:app --host 0.0.0.0 --port 
