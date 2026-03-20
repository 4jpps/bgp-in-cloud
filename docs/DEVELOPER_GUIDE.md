# Developer Guide

This guide provides instructions for setting up a development environment, running tests, and contributing to the BGP in Cloud IPAM project.

## Development Setup

1.  **Prerequisites:**
    -   Python 3.10+
    -   `pip` and `venv`

2.  **Clone the Repository:**

    ```bash
    git clone <repository-url>
    cd bgp-in-cloud-ipam
    ```

3.  **Create and Activate a Virtual Environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

4.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    pip install -r requirements-dev.txt # For running tests
    ```

5.  **Run the Application:**

    ```bash
    uvicorn bic.webapp:app --reload
    ```

## Running Tests

The project uses `pytest` for testing. To run the test suite:

```bash
python -m pytest
```

## Code Style and Linting

This project uses `black` for code formatting and `flake8` for linting. Ensure you have these installed in your development environment.

-   **Format Code:** `black .`
-   **Lint Code:** `flake8 .`

## Contributing

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes and ensure all tests pass.
4.  Submit a pull request with a clear description of your changes.
