# syntax=docker/dockerfile:1
FROM python:3
ENV PYTHONUNBUFFERED 1

# Setup Django App
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --upgrade pip setuptools && \
    pip install --no-cache-dir -r requirements.txt
COPY . /app/