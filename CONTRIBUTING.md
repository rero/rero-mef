<!--
SPDX-FileCopyrightText: Fondation RERO+
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Contributing

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

## Types of Contributions

### Report Bugs

Report bugs at https://github.com/rero/rero-mef/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

### Fix Bugs

Look through the GitHub issues for bugs. Anything tagged with "bug"
is open to whoever wants to implement it.

### Implement Features

Look through the GitHub issues for features. Anything tagged with "feature"
is open to whoever wants to implement it.

### Write Documentation

RERO MEF could always use more documentation, whether as part of the
official RERO MEF docs, in docstrings, or even on the web in blog posts,
articles, and such.

### Submit Feedback

The best way to send feedback is to file an issue at
https://github.com/rero/rero-mef/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

## Get Started!

Ready to contribute? Here's how to set up `rero-mef` for local development.

1. Fork the `rero/rero-mef` repo on GitHub.
2. Clone your fork locally:

   ```console
   $ git clone git@github.com:your_name_here/rero-mef.git
   ```

3. Install your local copy into a virtualenv. Assuming you have
   virtualenvwrapper installed, this is how you set up your fork for local
   development:

   ```console
   $ mkvirtualenv rero-mef
   $ cd rero-mef/
   $ pip install -e .[all]
   ```

4. Create a branch for local development:

   ```console
   $ git checkout -b name-of-your-bugfix-or-feature
   ```

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass tests:

   ```console
   $ uv run poe run_tests
   ```

   The tests will provide you with test coverage and also check PEP8
   (code style), PEP257 (documentation), and flake8.

6. Commit your changes and push your branch to GitHub:

   ```console
   $ git add .
   $ git commit -s \
       -m "component: title without verbs" \
       -m "* NEW Adds your new feature." \
       -m "* FIX Fixes an existing issue." \
       -m "* BETTER Improves an existing feature." \
       -m "* Changes something that should not be visible in release notes."
   $ git push origin name-of-your-bugfix-or-feature
   ```

7. Submit a pull request through the GitHub website.

## Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests and must not decrease test coverage.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring.
3. The pull request should work for Python 3.9 through 3.12. Check
   https://github.com/rero/rero-mef/actions
   and make sure that the tests pass for all supported Python versions.
