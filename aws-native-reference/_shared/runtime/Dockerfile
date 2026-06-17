# Shared AgentCore Runtime image (ARM64) — Bedrock AgentCore container contract.
# Build per-agent by copying that agent's code in and setting AGENT_MODULE.
FROM --platform=linux/arm64 python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LLM_PROVIDER=bedrock \
    CONNECTOR_MODE=live

WORKDIR /app

# Agent code + shared platform are copied by the per-agent build context.
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

# AgentCore Runtime contract: port 8080, /invocations + /ping
EXPOSE 8080
ENTRYPOINT ["python", "serve.py"]
