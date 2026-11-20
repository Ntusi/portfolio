# ntusekhomngadi.com

My portfolio. One static page, served from a private S3 bucket through CloudFront, with HTTPS from ACM and DNS in Route 53. No servers, no framework, no build tools beyond Python.

```
content/projects.json      <- the file you edit: AI work, cloud work, things I'm building, certifications
site/template.html         <- the page itself (hero, about, off the clock, contact)
site/assets/               <- photos, fonts, favicon, share image
build.py                   <- checks projects.json and writes the finished site to dist/
infra/portfolio-site.yaml  <- CloudFormation: S3, CloudFront, ACM, Route 53, GitHub deploy role
scripts/deploy-infra.sh    <- creates or updates the AWS stack
scripts/deploy-site.sh     <- builds and publishes the site
.github/workflows/deploy.yml  <- publishes automatically when you push to main
```

## Add a new project

Open `content/projects.json` and copy an existing item into the right list: `ai`, `cloud` or `building`.

```json
{
  "title": "My new agent",
  "status": "In progress",
  "description": "One or two sentences on what it does and what was hard about it.",
  "stack": "Python, Amazon Bedrock, Strands Agents SDK",
  "link": { "label": "View the repo", "url": "https://github.com/Ntusi/my-new-agent" }
}
```

- `title` and `description` are required. `status`, `stack` and `link` are optional.
- A status containing "progress" shows in mustard. Anything else shows in white.
- Put the newest or best project first: the order in the file is the order on the page.
- Items are separated by commas. No comma after the last one in a list.
- New certification? Add a line to `certifications`.

Then push to `main`. GitHub Actions checks the file, builds the page and publishes it. The site updates in a minute or two. You can even do this from the GitHub website on your phone.

If something is wrong, the build stops before anything goes live and tells you where, for example:

```
Build stopped: ai[0] "My new agent" description: contains an em dash. Rewrite that bit.
Build stopped: projects.json is not valid JSON: line 14, column 5: ... Usually a missing comma or an extra one after the last item.
```

## Preview on your machine

```
python3 build.py --serve
```

Then open http://localhost:8000.

## First-time setup

Do this once, after Route 53 emails you that ntusekhomngadi.com registration is complete.

**1. Deploy the AWS stack and the site from CloudShell.** Upload `ntusekhomngadi-site.zip` (Actions, Upload file), then:

```
unzip -oq ntusekhomngadi-site.zip && cd ntusekhomngadi-site && GITHUB_REPO=Ntusi/portfolio bash scripts/deploy-infra.sh && bash scripts/deploy-site.sh
```

The stack takes 5 to 15 minutes, mostly CloudFront. It always deploys to us-east-1, because CloudFront only accepts certificates from there, so it doesn't matter which region CloudShell is in. When it finishes, it prints a table of outputs. Keep it open for step 3.

**2. Create the GitHub repo.** Make an empty repo called `portfolio` under Ntusi and push this folder to it. If you use a different name, rerun step 1 with `GITHUB_REPO=Ntusi/<that-name>`, because the deploy role only trusts that exact repo's `main` branch.

**3. Tell GitHub where to deploy.** In the repo: Settings, Secrets and variables, Actions, Variables tab. Add three repository variables from the outputs table:

| Variable | Value from outputs |
| --- | --- |
| `AWS_ROLE_ARN` | `DeployRoleArn` |
| `SITE_BUCKET` | `BucketName` |
| `DISTRIBUTION_ID` | `DistributionId` |

No AWS keys are stored anywhere. GitHub signs in with OIDC, and the role can only upload to this one bucket and clear this one distribution's cache.

## What it costs

| Item | USD | About |
| --- | --- | --- |
| Route 53 hosted zone | $0.50 a month | R9 |
| CloudFront | Free tier: 1 TB and 10 million requests a month | R0 |
| S3 storage and requests | Under a megabyte of storage, a handful of requests | Under R1 |
| ACM certificate, CloudFront Function, CloudFormation, IAM | Free | R0 |
| Domain renewal | Yearly, see your Route 53 registration invoice | |

So roughly R9 to R10 a month plus the yearly domain renewal. Rand amounts use about R16.80 to the dollar.

## Changing other parts of the page

The hero, about text, off the clock and contact sections live in `site/template.html`. Edit the text there and push. Keep the four `<!-- ... -->` markers where they are, because `build.py` puts the cards there.

To swap a photo, put the new file in `site/assets/` under a new name (for example `portrait-cutout-2.webp`) and update the references in `template.html`. Using a new name means browsers fetch it straight away instead of showing a cached copy.

## Rolling back

Bucket versioning keeps old copies for 30 days. The quickest rollback is to revert the commit on GitHub, which republishes the previous version.

## Fonts

Young Serif and Schibsted Grotesk are self-hosted from `site/assets/fonts/` under the SIL Open Font License (see `LICENSE-OFL.txt`).
