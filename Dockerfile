FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONBUFFERED 1

WORKDIR /backend
COPY poetry.lock pyproject.toml /backend/
RUN pip install -U pip && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root
COPY . ./
COPY ../.env ./.env
ENTRYPOINT [ "bash", "-c", "./entrypoint.sh"]