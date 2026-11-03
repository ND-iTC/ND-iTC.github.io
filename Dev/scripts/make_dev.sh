#!/usr/bin/env bash
# Create (or refresh) the dev copy of the site as its own git repo, ready to push.
#   scripts/make_dev.sh [target-dir]      default: ../ND-iTC-site-dev
#   ND_DEV_REPO=Dev ND_NO_GIT=1 scripts/make_dev.sh /path/to/Dev   a Dev/ folder for ND-iTC.github.io/Dev/ (no git repo)
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:-$SRC/../ND-iTC-site-dev}"
ORG="${ND_ORG:-ND-iTC}"
NAME="${ND_DEV_REPO:-ND-iTC-site-dev}"
URL="https://$(echo "$ORG" | tr '[:upper:]' '[:lower:]').github.io/$NAME/"

mkdir -p "$DEST"
rsync -a --delete --exclude '.git' --exclude '.DS_Store' --exclude '.github' --exclude 'HANDOFF.md' "$SRC/" "$DEST/"
cd "$DEST"
ND_BASE_URL="$URL" python3 scripts/build.py
# Show a banner on every page of the dev copy so nobody mistakes it for production.
python3 - <<'PY'
import glob, re
banner = '<div style="background:#7ef0c4;color:#0d1526;text-align:center;padding:.4rem;font:600 14px system-ui">DEVELOPMENT PREVIEW &middot; not the published ND-iTC site</div>'
for f in ['index.html', 'TD/tech_dec.html', 'TD/tech_dec_arch.html', 'map/ndcpp-4.0.html', 'AWL/NDcPP_allowed_with_list.html', 'AWL/FW_allowed_with_list.html', 'training/index.html']:
    h = open(f, encoding='utf-8').read()
    if 'DEVELOPMENT PREVIEW' not in h:
        h = h.replace('<body>\n', '<body>\n' + banner + '\n', 1)
        h = h.replace('<head>', '<head>\n<meta name="robots" content="noindex">', 1)
        open(f, 'w', encoding='utf-8').write(h)
PY
printf 'User-agent: *\nDisallow: /\n' > robots.txt
if [ -z "${ND_NO_GIT:-}" ]; then
  [ -d .git ] || { git init -q -b main; }
  git add -A && git commit -q -m "Dev copy of the redesigned ND-iTC site" || true
fi
echo
echo "Dev copy ready in: $DEST"
echo "Will publish at:   $URL"
if command -v gh >/dev/null; then
  echo "Create + push:     gh repo create $ORG/$NAME --public --source . --push"
else
  echo "1. Create an empty repo $ORG/$NAME on GitHub (no README)."
  echo "2. git remote add origin https://github.com/$ORG/$NAME.git && git push -u origin main"
fi
echo "3. Repo Settings > Pages > Deploy from branch: main / (root)."
