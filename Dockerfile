FROM python:3.7

WORKDIR /opt/app

LABEL org.opencontainers.image.source https://github.com/uwcirg/helloworld-confidential-backend-sof
ARG VERSION_STRING
ENV VERSION_STRING=$VERSION_STRING

COPY requirements.txt .
RUN pip install --requirement requirements.txt

COPY . .

ENV FLASK_APP=backend.app:create_app() \
    PORT=5000

EXPOSE "${PORT}"

CMD gunicorn --bind "0.0.0.0:${PORT:-5000}" ${FLASK_APP}
