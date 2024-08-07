FROM python:3.10.14

MAINTAINER tools@digital.trade.gov.uk

RUN apt-get update && apt-get install -qq build-essential \
                                          libpq-dev \
                                          python3-dev \
                                          libffi-dev \
                                          libssl-dev \
                                          git \
                                          postgresql-client \
                                          libzbar-dev \
                                          libzbar0 

WORKDIR /app

COPY . /app

RUN pip install -r /app/requirements.txt

RUN pip install honcho

CMD honcho start

EXPOSE 8000
