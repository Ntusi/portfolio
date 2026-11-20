#!/usr/bin/env bash
# Builds the site and publishes it. Same script in CloudShell and in GitHub Actions.
#   bash scripts/deploy-site.sh
set -euo pipefail
cd "$(dirname "$0")/.."
STACK="${STACK:-ntusekhomngadi-site}"

python3 build.py

output() {
  aws cloudformation describe-stacks --region us-east-1 --stack-name "$STACK" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text
}
BUCKET="${SITE_BUCKET:-$(output BucketName)}"
DIST_ID="${DISTRIBUTION_ID:-$(output DistributionId)}"
LONG="public, max-age=86400"
SHORT="public, max-age=300"

# 1. Mirror dist/ to the bucket and remove anything you deleted locally.
aws s3 sync dist/ "s3://$BUCKET" --delete --only-show-errors --cache-control "$LONG"
# 2. Re-upload files whose type the CLI can guess wrong, with the right type.
for pair in "webp:image/webp" "woff2:font/woff2" "svg:image/svg+xml" "jpg:image/jpeg" "png:image/png"; do
  ext="${pair%%:*}"; type="${pair#*:}"
  aws s3 cp dist/ "s3://$BUCKET/" --recursive --only-show-errors --exclude "*" --include "*.$ext" --content-type "$type" --cache-control "$LONG"
done
# 3. Pages last, with a short cache so updates show up fast.
aws s3 cp dist/ "s3://$BUCKET/" --recursive --only-show-errors --exclude "*" --include "*.html" --content-type "text/html; charset=utf-8" --cache-control "$SHORT"
for f in robots.txt:text/plain sitemap.xml:application/xml; do
  aws s3 cp "dist/${f%%:*}" "s3://$BUCKET/${f%%:*}" --only-show-errors --content-type "${f#*:}" --cache-control "$SHORT"
done
# 4. Clear CloudFront's copy.
aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/*" --query 'Invalidation.Id' --output text >/dev/null
echo "Published. Live at https://ntusekhomngadi.com within a minute or two."
