#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -d .venv ]]; then
  python -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt

python - <<'PY'
from app import app
import io

client = app.test_client()

resp = client.get('/')
print('GET / ->', resp.status_code)

payload = {
    'target': 'markdown',
    'file': (io.BytesIO('demo text'.encode('utf-8')), 'demo.txt')
}
resp = client.post('/convert', data=payload, content_type='multipart/form-data')
print('POST /convert ->', resp.status_code)
print('output filename ->', resp.headers.get('Content-Disposition'))
print('output preview ->', resp.data.decode('utf-8', errors='ignore'))
PY

echo "Demo completed."
