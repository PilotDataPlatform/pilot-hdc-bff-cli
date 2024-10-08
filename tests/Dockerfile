FROM docker-registry.ebrains.eu/hdc-services-image/base-image:python-3.10.14-v1 AS bff-cli-image

COPY . .
RUN poetry install --no-dev --no-root --no-interaction
RUN chmod +x gunicorn_starter.sh

RUN chown -R app:app /app
USER app

CMD ["./gunicorn_starter.sh"]
