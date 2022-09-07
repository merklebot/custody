# Custody

## Develop

You need [pyenv](https://github.com/pyenv/pyenv) and [poetry](https://python-poetry.org/) available in development environment.

1. Setup Python version specified in `.python-version`

```console
pyenv install
```

2. Prepare virtual environment with required dependencies and activate it

```console
poetry install
poetry shell
```

3. Setup pre-commit git hooks to automate code quality check

```console
poetry run pre-commit install
```

4. Create `.env` and specify arguments

```console
cp .env.example
```

5. Run migrations

```console
alembic upgrade head
```

6. Run app

On a localhost

```console
python -m custody
```

Or in a container

```console
docker compose up
```

## Deploy

1. Create docker config for each environment variable required in `.env.example`

```console
echo "myvalue" | docker config create myenvvariable -
```

Also ensure each of them mentioned in `config` and `environment` sections in a service definition in `docker-compose.prod.yml`

2. Deploy stack to Docker Swarm cluster

```console
docker stack deploy -c docker-compose.yml -c docker-compose.prod.yml <stack_name>
```
