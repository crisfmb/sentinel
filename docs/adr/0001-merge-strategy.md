# ADR 0001: Merge strategy under signed-commits requirement

## Status

Accepted — 2026-05-27

## Context

Sentinel's `main` branch requires signed commits via a repository ruleset. This interacts with GitHub's three merge strategies as follows:

- **Merge commit** — GitHub creates and signs a new merge commit with its web-flow key. ✅
- **Squash and merge** — GitHub creates and signs a new squashed commit with its web-flow key. ✅
- **Rebase and merge** — GitHub rewrites each branch commit onto `main`, which strips signatures and cannot be re-signed by GitHub. ❌

GitHub's own documentation confirms the rebase incompatibility:

> "When using the Rebase and Merge option on a pull request, it's important to note that the commits in the head branch are added to the base branch without commit signature verification. When you use this option, GitHub creates a modified commit, using the data and content of the original commit. This means that GitHub didn't truly create this commit, and can't therefore sign it as a generic system user. GitHub doesn't have access to the committer's private signing keys, so it can't sign the commit on the user's behalf."
>
> — GitHub Docs, *About commit signature verification*

GitHub's web UI surfaces this directly when the merge is attempted:

> *"Base branch requires signed commits. Rebase merges cannot be automatically signed by GitHub."*

A separate incident on 2026-05-27 produced *"Dependabot couldn't access the repository"* on two PRs. Investigation showed this is GitHub's generic transient-error string, not a ruleset cascade. Resolved by `@dependabot recreate`. Recorded here so future encounters skip re-investigation.

## Decision

Allow **merge commit** and **squash and merge**. Disable **rebase and merge** in repository settings — it is incompatible with the signed-commits requirement.

Per-PR choice:

- **Squash** for atomic changes (typos, single-purpose features) and for bot PRs whose branch commits are unsigned — squash collapses them into one GitHub-signed commit.
- **Merge commit** for larger PRs where branch history tells a useful story (multi-step refactors with intentional intermediate states by a contributor whose commits are locally signed).

## Consequences

- Commits added directly to `main` are always signed: by GitHub for squash and merge-commit operations performed via the web UI.
- Commits reachable via merge-commit *parents* are signed only if the contributor signs locally. Bot commits will be unsigned in that case. Squashing bot PRs avoids leaving unsigned commits reachable from `main`.
- Contributors expecting rebase-and-merge as the default merge style will see GitHub's incompatibility warning when attempting it; this ADR is the answer to "why."

## References

- [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [About commit signature verification](https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification)
- [About merge methods on GitHub](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/about-merge-methods-on-github)
