# Contributing

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given. You can contribute in many ways:

## Types of Contributions

### Report Bugs

Report bugs at <https://github.com/gee-community/geemap/issues>.

If you are reporting a bug, please include:

-   Your operating system name and version.
-   Any details about your local setup that might be helpful in troubleshooting.
-   Detailed steps to reproduce the bug.

### Fix Bugs

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help wanted" is open to whoever wants to implement it.

### Implement Features

Look through the GitHub issues for features. Anything tagged with "enhancement" and "help wanted" is open to whoever wants to implement it.

### Write Documentation

geemap could always use more documentation, whether as part of the official geemap docs, in docstrings, or even on the web in blog posts, articles, and such.

### Submit Feedback

The best way to send feedback is to file an issue at <https://github.com/gee-community/geemap/issues>.

If you are proposing a feature:

-   Explain in detail how it would work.
-   Keep the scope as narrow as possible, to make it easier to implement.
-   Remember that this is a volunteer-driven project, and that contributions are welcome :)

## Get Started

Ready to contribute? Here's how to set up _geemap_ for local development.

1. Fork the [geemap](https://github.com/gee-community/geemap) repo on GitHub.

2. Clone your fork locally:

    ```
    git clone git@github.com:your_name_here/geemap.git
    ```

3. Install your local copy into a conda env. Assuming you have conda installed, this is how you set up your fork for local development:

    ```
    conda create -n geemap-test python
    ```

    ```
    conda activate geemap-test
    ```

    ```
    cd geemap/
    ```

    ```
    pip install -e .
    ```

4. Create a branch for local development:

    ```
    git checkout -b name-of-your-bugfix-or-feature
    ```

    Now you can make your changes locally.

5. When you're done making changes, ensure your code passes all local formatting and testing checks before submitting. We enforce strict code quality to keep the pipeline clean:

    Run the linters to check for style and syntax errors:
    ```bash
    flake8 geemap tests
    ```

    Run the test suite to ensure no existing features are broken:
    ```bash
    pytest
    ```

    *(Optional but recommended)* Test across multiple Python versions using tox:
    ```bash
    tox
    ```
    
    To get the necessary testing tools, install them into your conda env: 
    `pip install pyproject-flake8 pytest tox`

6. Commit your changes and push your branch to GitHub:

    ```bash
    git add .
    git commit -m "Your detailed description of your changes."
    git push origin name-of-your-bugfix-or-feature
    ```

7. Submit a pull request through the GitHub website.

## Pull Request Guidelines and CI/CD Checks

To ensure a smooth review process and keep the automated pipelines passing, please check that your pull request meets the following guidelines before submission:

### 1. Code Quality & Automated Checks
* **Pass the CI/CD Pipeline:** Your PR must pass all automated GitHub Actions checks. You can monitor these at <https://github.com/gee-community/geemap/actions>.
* **Python Compatibility:** The PR must work for Python 3.12-3.13. Ensure tests pass for all currently supported Python versions.
* **Linting:** Code must be free of `flake8` errors. 

### 2. Testing
* **Include Tests:** If you are adding a new feature or fixing a bug, include the corresponding `pytest` functions in the `tests/` directory.
* **Reproducibility:** Ensure your tests can be run locally by anyone replicating your environment.

### 3. Documentation
* **Docstrings:** Any new functionality must be encapsulated in a function or class with a complete, descriptive docstring.
* **README Updates:** If your PR adds a major feature, add it to the feature list in `README.md`.
* **Tutorials:** If applicable, consider adding a short Jupyter Notebook example in the examples directory to demonstrate how the new feature works.

### 4. PR Structure
* **Descriptive Title:** Use a clear and descriptive title for your PR (e.g., `Fix: resolving overlapping text in XYZ widget`).
* **Detailed Description:** Explain *what* changes you made, *why* you made them, and link to any relevant open issues (e.g., `Resolves #1234`).
* **Keep it Modular:** Try to keep the scope of the PR as narrow as possible. Large, sprawling PRs are much harder to review and merge.
