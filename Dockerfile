FROM python:3.9-buster

WORKDIR /usr/src/app

ENV TZ=America/Toronto

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    apt-get update && \
    apt-get install -y vim-tiny less && \
    ln -s /usr/bin/vim.tiny /usr/bin/vim && \
    rm -rf /var/lib/apt/lists/*
COPY . .
RUN pip install --no-cache-dir poetry==1.2.0
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev --no-root --no-interaction
RUN chmod +x gunicorn_starter.sh

CMD ["./gunicorn_starter.sh"]
