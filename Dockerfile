FROM python:3.11-alpine

COPY requirements.txt /app/

WORKDIR /app

# we need a bunch dependencies to build the psycopg2 package, but we don't them need to run it afterwards
RUN \
    apk add --no-cache --virtual .build gcc python3-dev musl-dev postgresql-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del --no-cache .build

# install library needed for postgres interface
RUN apk add --no-cache postgresql-libs bash

COPY . /app

ENTRYPOINT ["python", "main.py"]