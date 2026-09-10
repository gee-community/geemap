# 🚀 Releasing geemap

## Overview

The `geemap` release process is aligned with the **weekly Earth Engine client library release**, with **Thursday** being the target release day.

Releases are created directly from the `master` branch using GitHub Actions and dynamic versioning (`hatch-vcs`).

---

## 📅 Step-by-Step Release Instructions

### 1. Trigger the Release Workflow
1. Navigate to the **[Actions](https://github.com/gee-community/geemap/actions)** tab on GitHub.
2. Under **Workflows** on the left, select **`Release`** (or go to `.github/workflows/release.yml`).
3. Click **Run workflow**:
   - **Branch:** `master`
   - **Version number to release:** Enter the target version (e.g., `0.39.0`).
   - **Publish immediately:** Leave as `true` (or set `false` to generate a draft first).
4. Click **Run workflow**.

### 2. Verify Automated Publishing
1. **GitHub Release**: Verify the release was created under the **[Releases](https://github.com/gee-community/geemap/releases)** page with auto-generated release notes.
2. **PyPI Publishing**: Once the GitHub Release is published, the **`Publish to PyPI`** workflow triggers automatically. Verify the new version is live on [PyPI](https://pypi.org/project/geemap).
3. **Conda-Forge**: The Conda-Forge bot will automatically create a feedstock PR within ~1 hour.
