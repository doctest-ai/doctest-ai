FROM python:3.12-slim

# git: uv/pip VCS installs; nodejs+npm: the Claude Code CLI runtime.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git nodejs npm \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g @anthropic-ai/claude-code

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /work
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
COPY suites ./suites
RUN uv sync --frozen --no-dev

ENV PATH="/work/.venv/bin:$PATH"
