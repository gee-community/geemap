# 🚀 Releasing geemap

## Overview

The `geemap` release cycle is aligned with the **weekly Earth Engine client library release**, with **Thursday** being the target stable release day. 

The process is automated using GitHub Actions for versioning, tagging, and branch synchronization. The Releaser's role is focused on initiating the workflows and validating the automated results.

---

## 📅 Weekly Release Day Responsibilities (Target: Thursday)

The releaser performs these steps on the target release day, starting with the final stable release of the previous cycle's work before immediately spinning up the new cycle's testing phase.

### 1. ✅ Finalize and Publish Stable Release

The goal here is to release the package that was tested during the previous week.

#### **A. Publish the Stable Release**

1.  **Go to Workflow Dispatch:** Navigate to the **Actions** tab on GitHub, select the **`Release-stable`** workflow.
2.  **Run Workflow:** Click **Run workflow** and enter the required inputs:
    * **Version:** Enter the final stable version number (e.g., **`0.37.0`**).
    * **Publish immediately:** Leave as `false` to review the draft release first.
3.  **Action:** The workflow automatically creates the stable tag (`v0.37.0`) and creates a **draft GitHub Release**.

#### **B. Check and Publish the Final Draft Release**

1.  Go to the **Releases** page and find the new **Draft Release** (`v0.37.0`).
2.  **Review the release notes.** They should include the differences from the last stable release tag.
3.  **Publish the Release.** This single action triggers:
    * Final PyPI/Conda-Forge deployment and Docker build.
    * The Post-Release Development Sync workflow.

#### **C. Finalize the Master Branch Sync**

1.  Go to the **Pull Requests** tab.
2.  Find the automated PR titled: **`chore: Sync master version to X.Y.Z.post0`**.
3.  **Verify:** Check that the deployment steps triggered by the final stable release are complete and successful.
4.  **Merge the Pull Request.** This updates the `master` branch, setting the development version.

#### **D. Synchronize Bug Fixes to Master**

After the post-release PR is merged, ensure any bug fixes made directly to the **previous week's release branch** (e.g., `v0.37.0-release`) are present on `master`.

<details>
<summary><b>Advanced: Synchronize Fixes using a GitHub Codespace</b></summary>

The most robust way to ensure fixes are moved to the `master` branch is by using a dedicated cloud workspace.

1.  **Launch Codespace:** Open a new **GitHub Codespace** directly on the `master` branch. 
    * Navigate to the `master` branch, click the **Code** dropdown, and select **Codespaces** -> **New codespace**.

2.  **Identify Fix Commits:** Determine which fix commits from the old release branch (e.g., `v0.37.0-release`) need to be applied to `master`. The log command below shows commits on the release branch that are NOT yet in `master`:
    ```bash
    # View commits on the release branch that are NOT in master
    git log master..v0.37.0-release --oneline
    ```

3.  **Perform Cherry-Pick:** For each fix commit identified, execute the `git cherry-pick` command in the Codespace terminal.
    ```bash
    # Replace <COMMIT_HASH> with the specific hash of the fix commit
    git cherry-pick <COMMIT_HASH> 
    # Repeat for all necessary fixes. Resolve any conflicts in the editor.
    ```

4.  **Push the Fixes:** Once all necessary fixes have been applied and committed (or cherry-picked) onto your local `master` branch, push the final changes.
    ```bash
    git push origin master
    ```
5.  **Close Codespace:** The synchronization is complete. You can close the Codespace.

</details>

---

### 2. 🏁 Start the Next Prerelease Cycle

Immediately after deploying the stable release, initiate the testing cycle for the next version.

#### **A. Initiate the Prerelease Workflow**

1.  **Determine the Next Version:** Choose the next version number (e.g., **`0.37.1`**).
2.  **Go to Workflow Dispatch:** Navigate to the **Actions** tab on GitHub, select the **`Release-prerelease`** workflow.
3.  **Run Workflow:** Click **Run workflow** and enter the required inputs:
    * **Version:** Enter the base version (e.g., `0.37.1`).
    * **RC Number:** Use `1`.
    * **Publish immediately:** Leave as `false`.
4.  **Action:** The workflow creates the tag (`v0.37.1rc1`) and creates a **draft GitHub Prerelease**.

#### **B. Check and Publish the Prerelease**

1.  Go to the **Releases** page and find the new **Draft Prerelease** (`v0.37.1rc1`).
2.  **Review the notes.** They should include the differences from the last stable release tag.
3.  **Publish the Prerelease.** This action triggers the downstream CI jobs to make the release candidate available for testing.

#### **C. Testing for the Week**

* Throughout the following week, test the newly published candidate using `pip install geemap==0.37.1rc1`.
* If bugs are found, fix them on the **`v0.37.1-release` branch**. Then, use the `Release-prerelease` workflow to increment the RC number and republish the prerelease following the steps above.
