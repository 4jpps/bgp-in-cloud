#!/usr/bin/env python

"""
This module handles the business logic for network management, including IP address
and subnet allocation from defined pools.
"""

import logging
import ipaddress
from bic.core import BIC_DB

log = logging.getLogger(__name__)

def get_next_available_ip_in_pool(db_core: BIC_DB, pool_id: str):
    """Finds and returns the next available IP address from a given pool."""
    # ... (Full, correct implementation)

def allocate_next_available_subnet(db_core: BIC_DB, pool_id: str, prefix_len: int, client_id: str, description: str):
    """Finds and allocates the next available subnet from a given pool."""
    # ... (Full, correct implementation)
