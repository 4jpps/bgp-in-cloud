# Contributing to BGP in the Cloud

We welcome contributions from the community, whether they are bug reports, feature requests, or code contributions to the core application.

## Bug Reports and Feature Requests

- **Bug Reports:** If you encounter a bug, please check the existing issues on GitHub to see if it has already been reported. If not, please open a new issue. Provide as much detail as possible, including steps to reproduce, error messages, and your operating environment.

- **Feature Requests:** We are always open to new ideas. Please open a GitHub issue to describe the feature you would like to see, why it would be useful, and any implementation ideas you may have.

## Code Contributions

### Versioning and Release Process

This project uses a developer-managed, date-based versioning scheme in the format `YYYY.MM.DD.HHmm`.

When preparing a new release, the following steps must be taken:

1.  **Update the Changelog:** Add a new version header to `CHANGELOG.md`. List all significant `Added`, `Changed`, `Fixed`, and `Removed` items under the new version.

2.  **Update the Version File:** The version is controlled by the `bic/__version__.py` file. To stamp a new version, developers using PowerShell should run the `stamp-version.ps1` script from the root of the repository. This will overwrite the file with the current UTC date and time in the correct format.

    ```powershell
    .\stamp-version.ps1
    ```

3.  **Commit the Changes:** Commit the updated `CHANGELOG.md` and `bic/__version__.py` files with a message like `Release: Version YYYY.MM.DD.HHmm`.

### Contributor License Agreement (CLA)

For any contributions to the core codebase, you will be required to sign a Contributor License Agreement (CLA). This ensures that Jeff Parrish PC Services has the necessary rights to include your work in the proprietary product. Please contact us to initiate this process.
