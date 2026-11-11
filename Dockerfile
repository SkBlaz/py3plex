# Build a wheel and its dependencies from the canonical pyproject metadata.
FROM python:3.11-slim AS build
WORKDIR /build
COPY pyproject.toml README.md MANIFEST.in LICENSE ./
COPY py3plex ./py3plex
COPY py3plex_mcp ./py3plex_mcp
RUN python -m pip wheel --wheel-dir /wheels .

FROM python:3.11-slim
LABEL maintainer="Blaž Škrlj <blaz.skrlj@ijs.si>"
LABEL description="Py3plex CLI with core Python dependencies"
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MPLBACKEND=Agg \
    MPLCONFIGDIR=/tmp/matplotlib
COPY --from=build /wheels /wheels
RUN python -m pip install --no-index --find-links=/wheels py3plex \
    && rm -rf /wheels \
    && useradd --create-home --uid 1000 py3plex \
    && mkdir /data \
    && chown py3plex:py3plex /data
USER py3plex
WORKDIR /data
ENTRYPOINT ["py3plex"]
CMD ["help"]
