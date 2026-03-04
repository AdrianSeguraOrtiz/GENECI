FROM python:3.11-slim AS builder

ARG ARACNE3_REF=3d8791a23e3bd8fd0d74f3b8d48f912e81d00f14

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    build-essential \
    cmake \
    git \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /build

RUN git clone https://github.com/califano-lab/ARACNe3.git /build/ARACNe3 \
  && git -C /build/ARACNe3 checkout "${ARACNE3_REF}" \
  && git -C /build/ARACNe3 submodule update --init --recursive

RUN grep -q '^#include <cstdint>$' /build/ARACNe3/include/ARACNe3/ARACNe3.hpp || \
    sed -i '/#include <vector>/a #include <cstdint>' /build/ARACNe3/include/ARACNe3/ARACNe3.hpp

RUN cmake -S /build/ARACNe3 -B /build/ARACNe3/build \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_CXX_STANDARD=17 \
      -DCMAKE_CXX_STANDARD_REQUIRED=ON \
      -DCMAKE_CXX_EXTENSIONS=ON \
      -DCMAKE_CXX_FLAGS="-std=gnu++17" \
  && cmake --build /build/ARACNe3/build -j"$(nproc)"

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    libgomp1 \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /build/ARACNe3/build/src/app/ARACNe3_app_release /app/bin/ARACNe3_app_release
COPY run_tool.sh /app/run_tool.sh
COPY run_tool.py /app/run_tool.py
COPY _run_tool_common.py /app/_run_tool_common.py

RUN chmod +x /app/run_tool.sh /app/bin/ARACNe3_app_release

ENTRYPOINT ["/app/run_tool.sh"]
