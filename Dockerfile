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
CMD ["python", "-m", "custody"]
