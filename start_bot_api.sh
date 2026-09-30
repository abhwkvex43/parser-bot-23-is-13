#!/bin/bash
# Start local Telegram Bot API server (raises file upload limit from 50 MB to 2 GB)
# Requires API_ID and API_HASH in .env (from https://my.telegram.org)
cd "$(dirname "$0")"

# Parse .env for API_ID / API_HASH
API_ID=$(grep -E '^API_ID=' .env | cut -d'=' -f2- | tr -d '[:space:]')
API_HASH=$(grep -E '^API_HASH=' .env | cut -d'=' -f2- | tr -d '[:space:]')
PORT=$(grep -E '^LOCAL_BOT_API_URL=' .env | cut -d'=' -f2- | sed 's#.*:##' | tr -d '[:space:]')
PORT=${PORT:-8081}
DATA_DIR=$(grep -E '^LOCAL_BOT_API_DIR=' .env | cut -d'=' -f2- | tr -d '[:space:]')
DATA_DIR=${DATA_DIR:-./telegram-bot-api-data}

if [ -z "$API_ID" ] || [ -z "$API_HASH" ]; then
    echo "ERROR: API_ID or API_HASH not set in .env"
    echo "Get them from https://my.telegram.org -> API development tools"
    exit 1
fi

mkdir -p "$DATA_DIR" logs
echo "Starting telegram-bot-api on port $PORT (data dir: $DATA_DIR)"
echo "API_ID=$API_ID"
echo "Press Ctrl+C to stop"

exec ./telegram-bot-api/build/telegram-bot-api.exe \
    --api-id="$API_ID" \
    --api-hash="$API_HASH" \
    --local \
    --http-port="$PORT" \
    --dir="$DATA_DIR" \
    --log="logs/telegram-bot-api.log" \
    --verbosity=1
