#!/bin/sh
set -eu

: "${CAMPUS_ORIGIN:?Set CAMPUS_ORIGIN to the public https:// URL in Render}"
: "${CAMPUS_SESSION_SECRET:?Set a stable CAMPUS_SESSION_SECRET in Render}"
case "$CAMPUS_ORIGIN" in
  https://*) ;;
  http://127.0.0.1:*|http://localhost:*) ;;
  *) echo 'CAMPUS_ORIGIN must be https:// for a public deployment' >&2; exit 1 ;;
esac

mkdir -p "$CAMPUS_DATA_DIR"
chown campus:campus "$CAMPUS_DATA_DIR"
exec su -s /bin/sh campus -c 'exec gunicorn --bind "0.0.0.0:${PORT:-10000}" --workers 1 --threads 4 --timeout 120 app:app'