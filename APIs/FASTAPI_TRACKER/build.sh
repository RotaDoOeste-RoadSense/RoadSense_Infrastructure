#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

docker build -t lightglue_tracker -f "${SCRIPT_DIR}/Dockerfile" "${SCRIPT_DIR}"
docker rm -f lightglue_tracker || true
docker run -it \
  -v "${SCRIPT_DIR}:/app" \
  --gpus='"device=0"' \
  --privileged \
  --rm \
  -p 8714:8714 \
  --ipc=host \
  --ulimit memlock=-1 \
  --ulimit stack=67108864 \
  --name lightglue_tracker \
  lightglue_tracker bash
