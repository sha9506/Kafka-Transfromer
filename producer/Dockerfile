FROM python:3.9-slim

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONIOENCODING=utf-8

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the producer script
COPY producer.py .

# Optional: Add debugging to see what's in the container
RUN echo "Files in /app directory:" && ls -la /app/

# Run the producer with unbuffered output
CMD ["python", "-u", "producer.py"]