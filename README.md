# oss-twin

Keep a public OSS repo and its private mirror structurally aligned.

Many OSS maintainers run a private sister repo alongside their public one (atrib + atrib-internal, foo + foo-internal). The private repo holds operator memory, design specs with rejected alternatives, vendor IDs, deploy notes, and anything else that shouldn't be public but is too valuable to lose to git history archaeology. **oss-twin manages the boundary**: it scaffolds the mirror, gates the public repo against private paths leaking back in, and moves files cleanly across the boundary when you decide something needs to be private.

It pairs with [`textleaks`](https://github.com/creatornader/textleaks) (catches narrative leaks in file CONTENT) and the usual credential scanners (gitleaks, trufflehog). oss-twin owns the structural side: file LOCATION, not file content.

## Install

Install directly from GitHub (PyPI publication pending — the name is reserved on PyPI but the package is not yet uploaded):

```sh
pip install "git+https://github.com/creatornader/oss-twin.git@v0.1.1"
```

Or run as a `pre-commit` hook (see below). The pre-commit framework handles the install for you.

## Use

```sh
oss-twin scaffold-config    # write a starter .oss-twin.yaml
oss-twin init               # scaffold the private mirror at the configured path
oss-twin check              # fail if any private_paths exist in the public tree
oss-twin move docs/handoffs/ # move that path from public to the mirror
oss-twin status             # show where each private path currently lives
```

Exit code on `check`: `0` if clean, `1` if any private path leaked into the public tree. Wire into CI.

## Pre-commit hook

```yaml
repos:
  - repo: https://github.com/creatornader/oss-twin
    rev: v0.1.0
    hooks:
      - id: oss-twin-check
```

## Config (`.oss-twin.yaml`)

Lives at the public repo root. Committed.

```yaml
version: 1

mirror:
  path: ../my-repo-internal              # relative to public repo root, or absolute
  remote: git@github.com:user/my-repo-internal.git  # optional
  visibility: private

private_paths:
  - docs/handoffs/
  - docs/internal/
  - .remember/
  - thoughts/

mirror_scaffold:
  - docs/
  - docs/handoffs/
```

`private_paths` patterns:
- Trailing `/` means "directory and contents."
- Plain names match files exactly.
- Glob patterns work via fnmatch (`docs/*.internal.md`).

## Typical workflow

```sh
# Day 0: existing public repo, want to add a mirror
cd ~/repos/my-public-repo
oss-twin scaffold-config       # writes .oss-twin.yaml
# edit .oss-twin.yaml to confirm mirror path + private_paths
git add .oss-twin.yaml && git commit -m "chore: configure oss-twin"

# Scaffold the mirror
oss-twin init                  # creates ../my-public-repo-internal/ with CLAUDE.md + .gitignore

# Optionally, create the GitHub side privately
cd ../my-public-repo-internal
gh repo create user/my-public-repo-internal --private --source . --push

# Later: realize a file in the public repo should be private
cd ~/repos/my-public-repo
oss-twin move docs/handoffs/internal-stuff.md
# review, commit on both sides

# In CI:
oss-twin check                 # exits 1 if any private path leaked back in
```

## What this is NOT

- **Not a sync tool.** It doesn't bidirectionally keep two repos in lockstep. `move` is one-shot and explicit.
- **Not a content scanner.** Use [textleaks](https://github.com/creatornader/textleaks) for narrative-leak detection in file content.
- **Not a credential scanner.** Use gitleaks + trufflehog for that.
- **Not a history rewriter.** If a private file already landed in public history, use `git-filter-repo` to scrub it (and consider deleting + recreating the GitHub repo to expunge PR refs).
- **Not a workflow orchestrator.** Each tool above stays focused. If you want a manifest that declares "for this repo, run textleaks + oss-twin + gitleaks + osv-scanner at these phases," that's a separate layer (not built yet).

## Roadmap

This is v0.1.0, a spike.

- **`oss-twin sync`**: bidirectional structural diff between public and mirror with explicit-confirmation hunks
- **`oss-twin watch`**: filesystem-watcher that flags new files matching `private_paths` the instant they're created
- **CI action**: a reusable composite GitHub Action that runs `oss-twin check` cleanly without needing a pip install step
- **Multi-mirror**: support more than one mirror per public repo (e.g., one for ops, one for strategy)

## Related tools

oss-twin is one layer of a three-tool stack for maintaining public OSS repos with private context:

| Tool | Concern | When to install |
|---|---|---|
| [**textleaks**](https://github.com/creatornader/textleaks) | Narrative-leak detection in file CONTENT (prose patterns, codenames) | Anywhere you write prose that could leak operator-internal context |
| **oss-twin** (this tool) | Structural mirror gate that fails if any path declared private exists in the public tree | When you have a `*-internal` mirror repo |
| [**oss-security-scan**](https://github.com/creatornader/oss-security-scan) | Reusable GitHub Actions workflow (typos + gitleaks + trufflehog + osv-scanner) | Every public OSS repo |

For the full stack wire-up pattern (one repo, all three tools), see [`oss-security-scan/examples/full-stack-starter/`](https://github.com/creatornader/oss-security-scan/tree/main/examples/full-stack-starter).

## Note for repos with prose linters

`.oss-twin.yaml` lists private paths as YAML VALUES (e.g. `private_paths: [docs/handoffs/, ...]`). The whole job of this config is to enumerate those paths so oss-twin can guard them. If your repo also runs a prose linter (Vale, an LLM-based audit, etc.), exempt `.oss-twin.yaml` from those scanners. Otherwise the linter will flag the path strings as private-material references and propose renames that would break the tool. Same applies to [`textleaks.yaml`](https://github.com/creatornader/textleaks).

## License

Apache 2.0. See [LICENSE](LICENSE).
