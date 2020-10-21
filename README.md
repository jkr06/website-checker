# Check website availability

Check the website availability by calling a url, and log the response time and http status.
Optionally, some pattern can be searched in the returned content. 

There are 2 components, a producer and a consumer.
Producer calls the websites, and logs the events to kafka.
Consumer reads the events from kafka and writes into postgres Database.

## Quickstart run locally

https://kafka.apache.org/quickstart
Download kafka release, extract and start zookeeper and kafka.

```
tar xvfz Downloads/kafka_2.13-2.6.0.tgz
cd kafka_2.13-2.6.0
bin/kafka-server-start.sh config/server.properties
bin/zookeeper-server-start.sh config/zookeeper.properties
```

Start Postgres

`
docker run --name postgres -e POSTGRES_PASSWORD=secret -p 5432:5432 -d postgres:latest
`

Create environment, create database and initialize database

```
poetry install
python initdb.py
```

Run producer

`
faust -A producer:app worker -l info --without-web
`

Run consumer

`faust -A consumer:app worker -l info --without-web`

## Unit tests

`make test`

It creates a docker container for postgres, then the database is created and initialized.
After that, the tests are run. After tests are completed, the database is destroyed and then the container.
 

## Production use
Sign up to Aiven services at https://console.aiven.io/signup.html.
Create a postgres and kafka service.
From the overview page in Aiven console, get the details and create a settings.local.yaml file with the following contents:

```
production:
  kafka_broker_url: ["kafka-12345.aivencloud.com:21677"]
  use_sasl: true
  kafka_user: *****
  kafka_password: *****
  ca_file: ./ca.pem
  client_key: ./client.key
  client_cert: ./client.cert
  database:
      dbname: websitecheck
      user: *****
      password: *****
      host: pg-12345.aivencloud.com
      port: 21664
  default_db: defaultdb
```
Create database and initialize database

`ENV_FOR_DYNACONF=production python initdb.py`

Run Producer

`
ENV_FOR_DYNACONF=production faust -A producer:app worker -l info --without-web
`

Run consumer

`
ENV_FOR_DYNACONF=production faust -A consumer:app worker -l info --without-web
`

### Thanks

faust(https://github.com/robinhood/faust)

aiopg(https://github.com/aio-libs/aiopg)

httpx(https://github.com/encode/httpx)
