# Rex CI bot — setup

One-time setup to run `frxnls:rex-code-reviewer` automatically on PRs as a bot
identity. Pairs with `examples/rex-review.yml`. See the README "CI" section for the
why/tradeoffs.

## 1. Register the GitHub App

Go to `https://github.com/organizations/<org>/settings/apps/new`
(org → **Settings** → **Developer settings** → **GitHub Apps** → **New GitHub App**),
where `<org>` owns the repos rex will review (e.g. `forked-up`).

- **Name:** `Rex Code Reviewer` (globally unique; try `Rex Reviewer FU` if taken)
- **Homepage URL:** anything, e.g. this repo's URL
- **Webhook:** uncheck **Active** (CI mints its own token; no webhook needed)
- **Repository permissions:**
  - **Pull requests → Read and write**
  - **Contents → Read-only**
  - (Metadata → Read-only is automatic)
- **Where can this GitHub App be installed?**
  - **Only on this account** if you'll review repos in this org only
  - **Any account** if you'll install it on another org too
- **Create GitHub App**

## 2. App ID + private key

On the App's **General** page:
- Note the **App ID** (numeric).
- **Private keys → Generate a private key** → downloads a `.pem`. Keep it safe; delete
  it locally after step 4.

## 3. Install the App

App page → **Install App** → install on the org → **Only select repositories** → pick
the repos that run rex.

## 4. Store secrets

In each repo that runs the workflow (or at org level to share). Replace `<owner/repo>`:

```bash
gh secret set REX_APP_ID          --repo <owner/repo> --body "1234567"
gh secret set REX_APP_PRIVATE_KEY --repo <owner/repo> < ~/Downloads/rex-*.private-key.pem
rm ~/Downloads/rex-*.private-key.pem    # don't leave the key on disk

# Claude auth — pick ONE:
# (a) subscription token (Pro/Max; run `claude setup-token` locally first):
gh secret set CLAUDE_CODE_OAUTH_TOKEN --repo <owner/repo> --body "<token>"
# (b) Console API key:
gh secret set ANTHROPIC_API_KEY       --repo <owner/repo> --body "sk-ant-..."
```

Org-level instead of per-repo: swap `--repo <owner/repo>` for `--org <org> --visibility all`
(or `--repos <repo1,repo2>`).

## 5. Add the workflow

Copy `examples/rex-review.yml` to `.github/workflows/rex-review.yml` in each repo you
want reviewed, on its default branch. If you used the API key in step 4, swap the
`CLAUDE_CODE_OAUTH_TOKEN` env line in the workflow for `ANTHROPIC_API_KEY`.

## 6. Make it gate merges

Repo → **Settings → Branches → Branch protection** (or a ruleset) on the default branch:
- **Require status checks to pass before merging** → add the **`rex`** check.

Now every PR triggers rex; merge is blocked until the `rex` job is green.

## Rotate / revoke

The private key is a credential. To rotate: App **General → Private keys → Generate**
(old key auto-revokes), then update `REX_APP_PRIVATE_KEY`. Same for the Claude token —
re-run `claude setup-token` or regenerate the API key in the Console.
