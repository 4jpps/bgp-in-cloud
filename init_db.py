"""
This script initializes the database.

It should be run once during the initial setup of the application.
"""

import os
from bic.core import BIC_DB

# Get the base directory of the project
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

print("Initializing database...")

# Instantiate the database core. In the modified version, this
# will no longer run migrations automatically, so we will call it explicitly.
db = BIC_DB(base_dir=BASE_DIR)

# Run the schema creation and initial data seeding
db.run_migrations()

print("Database initialization complete.")
