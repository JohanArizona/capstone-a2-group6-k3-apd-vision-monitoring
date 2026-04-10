FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (termasuk netcat untuk health check)
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements dan install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Expose port
EXPOSE 8000

# Run entrypoint script
ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "main:application", "--host", "0.0.0.0", "--port", "8000", "--reload"]