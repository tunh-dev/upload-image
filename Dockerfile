# Base image
FROM python:3.10

# Define environment variable to avoid buffering logs
ENV PYTHONUNBUFFERED=1

# Set workdir
WORKDIR /app

# Install system dependencies (nếu cần)
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy entire project
COPY . /app/

# Ensure uploads folder exists
RUN mkdir -p /app/static/uploads

# Expose port
EXPOSE 5000

# Start the app with Python (Flask built-in server)
CMD ["python", "main.py"]
