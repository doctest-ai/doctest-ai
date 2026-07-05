#!/bin/sh
# Build the host allowlist: baseline + per-run docs-arm hosts.
set -eu

ALLOWLIST=/etc/tinyproxy/allowlist.txt

# Baseline: the model API and the package index task setups install from.
cat > "$ALLOWLIST" <<EOF
api.anthropic.com
pypi.org
files.pythonhosted.org
EOF

# Docs-arm hosts, comma-separated (must be empty for no-docs-arm runs).
if [ -n "${EXTRA_ALLOWED_HOSTS:-}" ]; then
    echo "$EXTRA_ALLOWED_HOSTS" | tr ',' '\n' >> "$ALLOWLIST"
fi

echo "tinyproxy allowlist:" >&2
cat "$ALLOWLIST" >&2

exec tinyproxy -d -c /etc/tinyproxy/tinyproxy.conf
