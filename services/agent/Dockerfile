FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Install uv from official image
COPY --from=ghcr.io/astral-sh/uv:0.5.20 /uv /uvx /bin/

# Copy workspace packages
COPY pyproject.toml ./
COPY packages/cart ./packages/cart
COPY services/agent ./services/agent
COPY eval/menu ./eval/menu

# Install packages with system pip via uv
RUN uv pip install --system -e ./packages/cart -e ./services/agent

CMD ["python", "-m", "lajur_agent.worker", "start"]
