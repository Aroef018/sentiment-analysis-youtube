#!/usr/bin/env sh
set -eu

MODEL_DIR="${MODEL_DIR:-/app/models}"
ONNX_PATH="${ONNX_MODEL_PATH:-$MODEL_DIR/model.onnx}"
ONNX_DATA_PATH="${ONNX_MODEL_DATA_PATH:-$MODEL_DIR/model.onnx.data}"
ARCHIVE_URL="${MODEL_ARCHIVE_URL:-}"
ONNX_URL="${ONNX_MODEL_URL:-}"
ONNX_DATA_URL="${ONNX_MODEL_DATA_URL:-}"

mkdir -p "$MODEL_DIR"

need_download="true"
if [ -f "$ONNX_PATH" ]; then
  size_bytes=$(wc -c < "$ONNX_PATH" | tr -d ' ')
  if [ "$size_bytes" -gt 10485760 ]; then
    need_download="false"
  fi
fi

if [ "$need_download" = "true" ]; then
  if [ -n "$ARCHIVE_URL" ]; then
    echo "Downloading model archive from $ARCHIVE_URL"
    curl -fsSL "$ARCHIVE_URL" -o /tmp/model.tar.gz
    tar -xzf /tmp/model.tar.gz -C "$MODEL_DIR"
    rm -f /tmp/model.tar.gz
  elif [ -n "$ONNX_URL" ] && [ -n "$ONNX_DATA_URL" ]; then
    echo "Downloading ONNX model from $ONNX_URL"
    curl -fsSL "$ONNX_URL" -o "$ONNX_PATH"
    echo "Downloading ONNX model data from $ONNX_DATA_URL"
    curl -fsSL "$ONNX_DATA_URL" -o "$ONNX_DATA_PATH"
  else
    echo "WARNING: ONNX model not found and no download URL set." >&2
  fi
fi

exec "$@"
