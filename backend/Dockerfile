FROM python:3.12-slim

WORKDIR /app

COPY ./requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

# install tesseract and libreoffice
RUN apt-get update && apt-get install -y tesseract-ocr libreoffice

ARG CACHEBUST=1
COPY ./app /app

# EXPOSE 8000

CMD ["fastapi", "run", "main.py", "--port", "8000"]