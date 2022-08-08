FROM python:3-alpine

WORKDIR /app

COPY ./app /app
COPY ./requirements.txt /app/requirements.txt

RUN apk update \
    && apk upgrade \
    && apk add --no-cache gcc libffi-dev libc-dev \
    && pip3 install --upgrade pip \
    && pip install -r /app/requirements.txt \
    && rm -rf /var/cache/apk/*

EXPOSE 5000

CMD [ "gunicorn", "-b 0.0.0.0:5000", "app:app"]
