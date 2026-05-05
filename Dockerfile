FROM python:3.11-slim

WORKDIR /code

RUN apt-get update && apt-get install -y gcc libpq-dev python3-dev libjpeg-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
