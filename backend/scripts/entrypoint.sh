#!/usr/bin/env sh
set -eu

MODEL_DIR="${MODEL_DIR:-/app/models}"
ONNX_PATH="${ONNX_MODEL_PATH:-$MODEL_DIR/model.onnx}"
ONNX_DATA_PATH="${ONNX_MODEL_DATA_PATH:-$MODEL_DIR/model.onnx.data}"
ARCHIVE_URL="${MODEL_ARCHIVE_URL:-}"
ARCHIVE_GDRIVE_ID="${MODEL_ARCHIVE_GDRIVE_ID:-}"
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
    if echo "$ARCHIVE_URL" | grep -q "drive.google.com"; then
      python -m gdown --fuzzy "$ARCHIVE_URL" -O /tmp/model.tar.gz
    else
      curl -fsSL "$ARCHIVE_URL" -o /tmp/model.tar.gz
    fi
    tar -tzf /tmp/model.tar.gz >/dev/null 2>&1
    tar -xzf /tmp/model.tar.gz -C "$MODEL_DIR"
    rm -f /tmp/model.tar.gz
  elif [ -n "$ARCHIVE_GDRIVE_ID" ]; then
    echo "Downloading model archive from Google Drive id $ARCHIVE_GDRIVE_ID"
    python -m gdown "$ARCHIVE_GDRIVE_ID" -O /tmp/model.tar.gz
    tar -tzf /tmp/model.tar.gz >/dev/null 2>&1
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
