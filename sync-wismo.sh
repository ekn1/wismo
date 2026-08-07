#!/usr/bin/env bash
set -euo pipefail

SRC_WISMO_DASH="/home/scents-iq-ltd7/wismo/dashboard"
SRC_PUBLIC_WISMO="/home/scents-iq-ltd7/public-site/wismo"
DEPLOY_DIR="/home/scents-iq-ltd7/public-site/wismo-deploy"
REMOTE="origin"
BRANCH="master"
COMMIT_MSG="auto-sync: update WISMO pages from local dashboards"

if [ ! -d "$DEPLOY_DIR/.git" ]; then
  echo "ERROR: $DEPLOY_DIR is not a git repo"
  exit 1
fi

cd "$DEPLOY_DIR"

# Ensure we have latest remote refs
git fetch "$REMOTE" "$BRANCH" || true

# Copy dashboard files from wismo/dashboard
cp -f "$SRC_WISMO_DASH/index.html" "$DEPLOY_DIR/index.html"
cp -f "$SRC_WISMO_DASH/WISMO-Rider.html" "$DEPLOY_DIR/WISMO-Rider.html"

# Copy any other files from public-site/wismo that should be deployed
cp -f "$SRC_PUBLIC_WISMO/background.html" "$DEPLOY_DIR/background.html" 2>/dev/null || true
cp -f "$SRC_PUBLIC_WISMO/bi.html" "$DEPLOY_DIR/bi.html" 2>/dev/null || true
cp -f "$SRC_PUBLIC_WISMO/portal.html" "$DEPLOY_DIR/portal.html" 2>/dev/null || true
cp -f "$SRC_PUBLIC_WISMO/rider.html" "$DEPLOY_DIR/rider.html" 2>/dev/null || true
cp -f "$SRC_PUBLIC_WISMO/WISMO-Landing.html" "$DEPLOY_DIR/WISMO-Landing.html" 2>/dev/null || true

# Ensure .nojekyll exists
touch "$DEPLOY_DIR/.nojekyll"

# Stage and commit if there are changes
if git diff --quiet && git diff --cached --quiet; then
  echo "No changes to deploy"
  exit 0
fi

git add -A
git commit -m "$COMMIT_MSG"
git push "$REMOTE" "$BRANCH"
echo "Deployed to https://github.com/ekn1/wismo"
