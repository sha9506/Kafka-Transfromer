FROM python:3.11-slim

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONIOENCODING=utf-8

WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY consumer.py ./
CMD ["python", "-u", "consumer.py"]
