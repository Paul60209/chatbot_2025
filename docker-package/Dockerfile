FROM python:3.11.4

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y vim pkg-config libmariadb-dev
RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["python3", "-m" , "chainlit", "run", "app.py"] 