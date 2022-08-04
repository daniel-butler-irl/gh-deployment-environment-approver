FROM python:3-alpine

WORKDIR /app

COPY app.py /app/app.py
COPY requirements.txt /app/requirements.txt

RUN apk update \
    && apk upgrade \
    && apk add --no-cache gcc libffi-dev libc-dev \
    && pip3 install --upgrade pip \
    && pip install -r /app/requirements.txt \
    && rm -rf /var/cache/apk/*

EXPOSE 3000

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
