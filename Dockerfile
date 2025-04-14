FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PORT=8080

# Command to run the application
CMD exec python -m uvicorn src.app:app --host 0.0.0.0 --port $PORT --timeout-keep-alive 75