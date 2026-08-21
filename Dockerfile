# syntax=docker/dockerfile:1

FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml ./
COPY app ./app
COPY features ./features
COPY shared ./shared

RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim

RUN useradd --create-home --uid 1000 spp
COPY --from=builder /install /usr/local

WORKDIR /home/spp
COPY app ./app
COPY features ./features
COPY shared ./shared

USER spp

ENV PORT=8000
EXPOSE 8000

CMD ["python", "-m", "app"]
