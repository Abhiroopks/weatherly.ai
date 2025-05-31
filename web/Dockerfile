FROM python:3.10-alpine

COPY requirements.txt .
RUN apk add --no-cache build-base && pip3 install --upgrade pip
RUN pip install -r requirements.txt --no-cache-dir

WORKDIR /app
COPY . .