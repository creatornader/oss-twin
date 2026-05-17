# oss-twin

Keep a public OSS repo and its private mirror structurally aligned.

Many OSS maintainers run a private sister repo alongside their public one (atrib + atrib-internal, foo + foo-internal). The private repo holds operator memory, design specs with rejected alternatives, vendor IDs, deploy notes, and anything else that shouldn't be public but is too valuable to lose to git history archaeology. **oss-twin manages the boundary**: it scaffolds the mirror, gates the public repo against private paths leaking back in, and moves files cleanly across the boundary when you decide something needs to be private.

It pairs with [`leakguard`](https://github.com/creatornader/leakguard) (catches narrative leaks in file CONTENT) and the usual credential scanners (gitleaks, trufflehog). oss-twin owns the structural side: file LOCATION, not file content.

## Install

```sh
pip install oss-twin
```

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
- **Not a content scanner.** Use [leakguard](https://github.com/creatornader/leakguard) for narrative-leak detection in file content.
- **Not a credential scanner.** Use gitleaks + trufflehog for that.
- **Not a history rewriter.** If a private file already landed in public history, use `git-filter-repo` to scrub it (and consider deleting + recreating the GitHub repo to expunge PR refs).
- **Not a workflow orchestrator.** Each tool above stays focused. If you want a manifest that declares "for this repo, run leakguard + oss-twin + gitleaks + osv-scanner at these phases," that's a separate layer (not built yet).

## Roadmap

This is v0.1.0, a spike.

- **`oss-twin sync`**: bidirectional structural diff between public and mirror with explicit-confirmation hunks
- **`oss-twin watch`**: filesystem-watcher that flags new files matching `private_paths` the instant they're created
- **CI action**: a reusable composite GitHub Action that runs `oss-twin check` cleanly without needing a pip install step
- **Multi-mirror**: support more than one mirror per public repo (e.g., one for ops, one for strategy)

## License

Apache 2.0. See [LICENSE](LICENSE).
