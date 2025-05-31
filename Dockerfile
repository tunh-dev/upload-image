# Base image
FROM python:3.10

# Set working directory
WORKDIR /app

# Copy code
COPY . /app

# Install dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Create uploads folder if not exists
RUN mkdir -p /app/static/uploads

# Expose port
EXPOSE 5000

# Run app using Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
