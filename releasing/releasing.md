# Releasing

## Overview

The geemap release rotation lasts 2 weeks.

The first week consists of:

-   creating a release candidate,
-   deploying the release candidate to staging,
-   testing the release candidate, and
-   fixing any potential launch blockers.

The second week consists of:

-   pushing the release candidate to production, and
-   landing the launch (e.g. cleaning up, monitoring, etc.).

These responsibilities are handled by the "releaser". The releaser rotates every
two weeks. If you'd like to become a member of the release rotation, please
reach out!

## Releaser Responsibilities

### Week 1

#### **Monday:** Create and deploy a new release candidate to staging

1. Choose a version number. The version number follows
   [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html). In short,
   version numbers follow `vMAJOR.MINOR.PATCH`, where `MAJOR` is for breaking
   changes, `MINOR` is for new features, and `PATCH` is for bug fixes. You can
   see previous version numbers chosen by visiting the
   [Releases](https://github.com/gee-community/geemap/releases) page.

2. Checkout the appropriate release branch. The branch name should use the
   following format: `vMAJOR.MINOR`. The `PATCH` number is excluded from the
   branch name.

    - For `PATCH` version upgrades, checkout the existing release branch.
    - For major/minor version upgrades, create a new branch from `master`.

3. Bump the version number using `bump-my-version` (e.g.
   `bump-my-version bump <minor,major,patch>`). The version commit will be made
   to the release candidate branch directly. Verify the version number is
   as-expected to avoid problems further along.

4. Create a tag for this release (`git tag <tag-name>`). Tags for release
   candidates should use the following format: `vMAJOR.MINOR.PATCH-rc.RC_NUM`
   (e.g. `v0.32.0-rc.1`). `RC_NUM` starts at 1 and increments for each release
   candidate. Push the tag to GitHub with `git push origin <tag-name>`.

#### **Monday to Wednesday:** Test the release candidate

1. Switch to your test environment. Consider using a
   [Colab](https://colab.google/) notebook.

2. Install the release candidate by running the following command:
   `pip install git+https://github.com/gee-community/geemap.git@branch-name#egg=geemap`
   and replacing `branch-name` with the branch name. `pip` will install from the
   most recent commit on the release candidate branch.

3. Run through the example notebooks, testing both geemap and geemap core. If
   there are any launch blockers, file a bug and raise them to the rest of the
   team. The bugs must be fixed and tested before the build reaches production.

#### **Wednesday to Friday:** Fix launch-blockers and re-stage

Skip this section if there aren't any launch-blocking bugs.

1. Commit the fix. Make sure the commits are present on the necessary branches.

    - If the fix is for something present on both the `master` and release
      candidate branch, make the fix on the `master` branch and cherrypick it
      over to the release candidate branch.
    - Otherwise, make the fix on the release candidate branch.

2. Switch to the release candidate branch. Run `bump-my-version` to update the
   patch number.

3. Create a tag for this release. Increment `RC_NUM` for each release candidate.
   Push the tag to GitHub.

### Week 2

#### **Monday to Wednesday:** Deploy the release candidate to production

Before proceeding, make sure the launch blockers have been fixed.

1. Create a new
   [GitHub release](https://github.com/gee-community/geemap/releases) based on
   the most recent release candidate tag. When generating the release notes,
   compare against the most recent version that went to production (i.e. not a
   version with the `-rc` suffix).

2. Monitor the [actions](https://github.com/gee-community/geemap/actions)
   triggered by the release to make sure they pass. Verify the new version is
   present on [PyPi](https://pypi.org/project/geemap/).

3. Switch to the `master` branch to update the changelog. Replace
   `markdown_text` in
   [`changelog_update.py`](https://github.com/gee-community/geemap/blob/master/docs/changelog_update.py)
   with the release notes. Run the script and copy the output into
   [changelog.md](https://github.com/gee-community/geemap/blob/master/docs/changelog.md).

4. Switch to the `master` branch to update the version number. Cherrypick the
   version bump commit (e.g.
   [0.31.0 → 0.32.0](https://github.com/gee-community/geemap/pull/1924/commits/3c2f7548d12e3a7c5600b3cb72a0fa107cdbd983))
   into the `master` branch.
