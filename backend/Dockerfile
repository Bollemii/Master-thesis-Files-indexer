FROM python:3.13-slim-bookworm

WORKDIR /app

COPY ./requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

# install tesseract and libreoffice
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libreoffice \
    default-jre \
    libreoffice-java-common \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ARG CACHEBUST=1
COPY ./app /app

RUN mkdir -p /app/tmp

CMD ["fastapi", "run", "main.py", "--port", "8000"]