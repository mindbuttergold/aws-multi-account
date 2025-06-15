# template-repo

[![CodeQL](https://github.com/mindbuttergold/template-repo/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/mindbuttergold/template-repo/actions/workflows/github-code-scanning/codeql) [![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/mindbuttergold/template-repo/badge)](https://scorecard.dev/viewer/?uri=github.com/mindbuttergold/template-repo) [![OpenSSF Best Practices](https://www.bestpractices.dev/projects/10740/badge)](https://www.bestpractices.dev/projects/10740)

Template repo with foundational config and workflows applicable across all repository setups

## Included Components

This template repository provides the following components:
- README.md
- Minimal .gitignore
- MIT OSS License
- CODEOWNERS file
- Semantic Release config file and Github Actions workflow
  - Automatically handles repository releases based on Conventional Commit standards
- PR title validation Github Actions workflow
  - Ensures PR title complies with Conventional Commit standards for use with squash merging / semantic release automation
- Custom PR thumbs up check Github Actions workflow
  - Checks all open PRs in the repo for thumbs up reactions from at least 5 community members, excluding the PR author
  - If 5+ thumbs up on PR, automatically adds "community-approved" label to PR
  - If "community-approved" label was previously added, but thumbs up reduced to below 5, it removes the label
- Custom community approval label check
  - Checks if the "community-approved" label is present on the PR
  - Serves as a required check for PR mergeability

## Usage

Admin / maintainers of the mindbuttergold organization can use this template to create a new repository. The new repository will contain all of the files in this repository.

The only repo-specific changes that need to be made for the new repo are to this README. The badge URLs must be updated, and the openssf best practices self-certification process must be re-conducted for each repo.
