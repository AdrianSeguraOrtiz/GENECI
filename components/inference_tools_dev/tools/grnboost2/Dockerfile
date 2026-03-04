FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir arboreto==0.1.6

COPY run_tool.sh /app/run_tool.sh
COPY run_tool.py /app/run_tool.py
COPY _run_tool_common.py /app/_run_tool_common.py
COPY _arboreto_common.py /app/_arboreto_common.py

RUN chmod +x /app/run_tool.sh

ENTRYPOINT ["/app/run_tool.sh"]
