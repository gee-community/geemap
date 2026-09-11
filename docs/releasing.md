# 🚀 Releasing geemap

## Overview

The `geemap` release process is aligned with the **weekly Earth Engine client library release**, with **Thursday** being the target release day.

Releases are created directly from the `master` branch using GitHub Actions and dynamic versioning (`hatch-vcs`).

---

## 🔍 How to Determine the Version Number

Before triggering a release, the releaser needs to choose the target version number according to [Semantic Versioning](https://semver.org) (`MAJOR.MINOR.PATCH`).

### 1. Check the Latest Released Version
* On GitHub: Visit the **[Releases](https://github.com/gee-community/geemap/releases)** page (e.g., `v0.38.6`).
* In Git: Run `git describe --tags origin/master` or `git tag -l "v0.*" --sort=-v:refname | head -n 1`.

### 2. Inspect Changes Since the Last Release
Compare `master` against the previous tag to see all merged PRs and commits:
* On GitHub: Visit `https://github.com/gee-community/geemap/compare/<LATEST_TAG>...master`  
  *(Example: [`v0.38.6...master`](https://github.com/gee-community/geemap/compare/v0.38.6...master))*.
* In Git: Run `git log <LATEST_TAG>..origin/master --oneline`.

### 3. Choose the Version Bump (Major, Minor, or Patch)

Given the latest version `0.Y.Z` (e.g., `0.38.6`):

* **Patch Bump (`0.Y.Z+1` ➔ `0.38.7`):**
  * Use for routine maintenance releases containing **bug fixes**, **dependency bumps**, **documentation updates**, **type annotations**, or internal CI/build improvements without new user-facing APIs.
* **Minor Bump (`0.Y+1.0` ➔ `0.39.0`):**
  * Use when **new user-facing features**, **new interactive map tools/widgets**, **new backend integrations**, or new functions/modules are added in a backward-compatible manner.
* **Major Bump (`X+1.0.0` ➔ `1.0.0`):**
  * Reserved for major milestone releases or incompatible public API changes.

---

## 📅 Step-by-Step Release Instructions

The release process follows a safe **Draft ➔ Review ➔ Publish** workflow.

### Step 1: Trigger the Release Workflow (Creates Draft)
1. Navigate to the **[Actions](https://github.com/gee-community/geemap/actions)** tab on GitHub.
2. Under **Workflows** on the left, select **`Release`** (or go to [`.github/workflows/release.yml`](https://github.com/gee-community/geemap/actions/workflows/release.yml)).
3. Click **Run workflow**:
   * **Branch:** `master`
   * **Version number to release:** Enter the target version (e.g., `0.38.7` or `0.39.0`).
4. Click **Run workflow**.
5. The workflow will validate the version, tag `master` (e.g. `v0.38.7`), and create a **Draft Release** with auto-generated release notes.

### Step 2: Review and Publish the Release
1. Navigate to the **[Releases](https://github.com/gee-community/geemap/releases)** page on GitHub.
2. Find the newly created **Draft Release** and click **Edit**.
3. Review the auto-generated changelog notes and make any necessary edits or formatting adjustments.
4. Click **Publish release** (ensuring "Set as latest release" is checked).

### Step 3: Verify Automated PyPI & Conda-Forge Publishing
1. **PyPI Publishing**: Publishing the GitHub release in the web UI automatically triggers the **`Publish to PyPI`** workflow.
   * Check the **[Actions](https://github.com/gee-community/geemap/actions/workflows/publish.yml)** tab to verify the build and upload.
   * Verify the new package is live on [PyPI](https://pypi.org/project/geemap).
2. **Conda-Forge**: The Conda-Forge automation bot will detect the new release and open a feedstock update PR on [conda-forge/geemap-feedstock](https://github.com/conda-forge/geemap-feedstock) within ~1 hour.
