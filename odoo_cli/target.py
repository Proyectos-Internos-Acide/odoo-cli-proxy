"""Factory for creating an OdooClient connected to the migration target instance.

Reads TARGET_MIGRATION_URL, TARGET_MIGRATION_DB, TARGET_MIGRATION_USERNAME,
TARGET_MIGRATION_PASSWORD from the environment. Returns None if not configured.
"""

import os

from .client import OdooClient


def get_target_client():
    """Create an OdooClient for the target migration instance, or None if not configured."""
    url = os.getenv('TARGET_MIGRATION_URL', '').strip()
    db = os.getenv('TARGET_MIGRATION_DB', '').strip()
    username = os.getenv('TARGET_MIGRATION_USERNAME', '').strip()
    password = os.getenv('TARGET_MIGRATION_PASSWORD', '').strip()

    if not all([url, db, username, password]):
        return None

    verify = os.getenv('TARGET_MIGRATION_VERIFY_SSL', 'False').lower() == 'true'
    return OdooClient(url=url, db=db, username=username, password=password, verify_ssl=verify)
