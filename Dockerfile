FROM mhart/alpine-node:8

ENV DATABASE_URL="sqlite:///circleapp.db"

RUN apk add --update \
    python3

RUN mkdir /code
WORKDIR /code
ADD . /code

RUN apk add --no-cache --virtual .build-deps \
     build-base \
     libffi-dev \
     python3-dev \
  && pip3 install --no-cache-dir -r requirements.txt \
  && apk del .build-deps

EXPOSE 5000

# Command untuk development mode
CMD ["python3", "run.py"]
