FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /telegram_bot

COPY requirements.txt .

COPY . .

RUN apt-get update && apt-get install -y libmagic1
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]