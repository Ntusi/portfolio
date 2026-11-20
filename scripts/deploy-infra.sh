#!/usr/bin/env bash
# Creates or updates the AWS side of the site. Run from the repo root in CloudShell.
#   GITHUB_REPO=Ntusi/portfolio bash scripts/deploy-infra.sh
set -euo pipefail
cd "$(dirname "$0")/.."
DOMAIN="${DOMAIN:-ntusekhomngadi.com}"
STACK="${STACK:-ntusekhomngadi-site}"
REPO="${GITHUB_REPO:-}"

HZ=$(aws route53 list-hosted-zones-by-name --dns-name "$DOMAIN" --query "HostedZones[?Name=='${DOMAIN}.'].Id | [0]" --output text | cut -d/ -f3)
if [ -z "$HZ" ] || [ "$HZ" = "None" ]; then
  echo "No Route 53 hosted zone for $DOMAIN yet. Wait for the registration-complete email, then run this again."
  exit 1
fi

# Reuse GitHub's identity provider if the account already has one.
MAKE=true
if [ -n "$REPO" ]; then
  HAS=$(aws iam list-open-id-connect-providers --query "length(OpenIDConnectProviderList[?contains(Arn, 'token.actions.githubusercontent.com')])" --output text)
  OWNED=$(aws cloudformation describe-stack-resource --region us-east-1 --stack-name "$STACK" --logical-resource-id GitHubOIDCProvider >/dev/null 2>&1 && echo yes || echo no)
  if [ "$HAS" != "0" ] && [ "$OWNED" = "no" ]; then MAKE=false; fi
fi

echo "Deploying $STACK for $DOMAIN (hosted zone $HZ). Allow 5 to 15 minutes, mostly CloudFront."
aws cloudformation deploy --region us-east-1 --stack-name "$STACK" \
  --template-file infra/portfolio-site.yaml --capabilities CAPABILITY_NAMED_IAM --no-fail-on-empty-changeset \
  --parameter-overrides DomainName="$DOMAIN" HostedZoneId="$HZ" GitHubRepo="$REPO" CreateGitHubOIDCProvider="$MAKE"
aws cloudformation describe-stacks --region us-east-1 --stack-name "$STACK" --query 'Stacks[0].Outputs' --output table
