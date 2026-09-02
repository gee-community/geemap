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

3. Install your local copy into a virtual environment or conda env. Assuming you have conda installed, this is how you set up your fork for local development:

    ```bash
    conda create -n geemap-test python=3.12
    conda activate geemap-test
    cd geemap/
    pip install -e ".[dev]" pre-commit
    pre-commit install
    ```

    Alternatively, if using `uv`:

    ```bash
    cd geemap/
    uv sync
    pre-commit install
    ```

4. Create a branch for local development:

    ```bash
    git checkout -b name-of-your-bugfix-or-feature
    ```

    Now you can make your changes locally.

5. When you're done making changes, check that your changes pass pre-commit checks (including Black formatting and Pyrefly type checking) and tests:

    ```bash
    pre-commit run --all-files
    ```

    ```bash
    pytest
    ```

    You can also run Pyrefly type checking directly:

    ```bash
    uv run pyrefly check
    ```

6. Commit your changes and push your branch to GitHub:

    ```
    git add .
    ```

    ```
    git commit -m "Your detailed description of your changes."
    ```

    ```
    git push origin name-of-your-bugfix-or-feature
    ```

7. Submit a pull request through the GitHub website.

## Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put your new functionality into a function with a docstring, and add the feature to the list in README.md.
3. The pull request should work for Python 3.12-3.13. Check <https://github.com/gee-community/geemap/actions> and make sure that the tests pass for all supported Python versions.
