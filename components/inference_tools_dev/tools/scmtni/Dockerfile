FROM python:3.11-slim-bookworm AS builder

ARG SCMTNI_REF=2282e58e6d8e038194f3a4ebcdae2a785093eb33

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    build-essential \
    git \
    libgsl-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /build

RUN git clone https://github.com/Roy-lab/scMTNI.git /build/scMTNI \
  && git -C /build/scMTNI checkout "${SCMTNI_REF}" \
  && make -C /build/scMTNI/Code \
  && install -Dm755 /build/scMTNI/Code/scMTNI /build/out/scMTNI

FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libgsl-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /build/out/scMTNI /app/bin/scMTNI
COPY run_tool.sh /app/run_tool.sh
COPY run_tool.py /app/run_tool.py
COPY _run_tool_common.py /app/_run_tool_common.py

RUN chmod +x /app/run_tool.sh /app/bin/scMTNI

ENTRYPOINT ["/app/run_tool.sh"]
