FROM python:3.13-slim
LABEL maintainer="shafayetsadi.me"

# Installing uv
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"

ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1

ADD . /app
WORKDIR /app
RUN uv sync --frozen
EXPOSE 8000