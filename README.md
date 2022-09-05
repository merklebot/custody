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

2. Set database url in .env and activate it

```console
source .env.example
```

3. Run migrations

```console
alembic upgrade head
```


4. Run app

```console
python -m custody
```
