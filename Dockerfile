FROM python:3.10.6 as requirements-stage
WORKDIR /tmp
RUN pip install poetry
COPY ./pyproject.toml ./poetry.lock* /tmp/
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.10.6
WORKDIR /custody
COPY --from=requirements-stage /tmp/requirements.txt /custody/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /custody/requirements.txt
COPY ./custody /custody/custody
COPY ./tmp /custody/tmp
COPY ./alembic.ini /custody/alembic.ini
COPY ./start.sh /custody/start.sh
ENTRYPOINT ["/bin/bash" ,"start.sh"]
