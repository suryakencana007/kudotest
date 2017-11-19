FROM alpine:3.6

ENV DATABASE_URL="sqlite:///circleapp.db"

WORKDIR /usr/src/app
COPY . .

RUN apk add --update \
    python3 \
    build-base \
    libffi-dev \
    openssl-dev \
    python3-dev \
  && python3 -m ensurepip \
  && rm -r /usr/lib/python*/ensurepip \
  && pip3 install --upgrade pip setuptools \
  && if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi \
  && if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi \
  && rm -r /root/.cache \
  && rm -rf /var/cache/apk/*


RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["python", "run.py"]
