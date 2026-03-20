#!/usr/bin/env python
"""
This module handles the management of firewall rules, specifically NAT (MASQUERADE)
for private IP ranges that need to access the internet.
"""

import subprocess
from bic.core import BIC_DB, get_logger

# Initialize logger
log = get_logger(__name__)

def ensure_nat_rules(db_core: BIC_DB):
    """
    Ensures that the necessary iptables NAT rules for private ranges exist.

The private ranges are fetched from the 'nat_private_ranges' setting in the database,
    which should be a comma-separated list of CIDR networks (e.g., '172.30.0.0/16,10.0.0.0/8').

    Args:
        db_core: An instance of the BIC_DB class.
    """
    log.info("Ensuring iptables NAT rules are in place.")

    # Fetch private ranges from settings, with a fallback to an empty list
    private_ranges_str = db_core.get_setting('nat_private_ranges', '')
    if not private_ranges_str:
        log.warning("No 'nat_private_ranges' configured in settings. Skipping NAT rule check.")
        return

    private_ranges = [cidr.strip() for cidr in private_ranges_str.split(',')]

    for cidr in private_ranges:
        if not cidr:
            continue

        try:
            # Command to check if the NAT rule already exists. This is more reliable than checking output.
            check_cmd = ["sudo", "iptables", "-t", "nat", "-C", "POSTROUTING", "-s", cidr, "-j", "MASQUERADE"]
            log.debug(f"Checking for NAT rule with command: {' '.join(check_cmd)}")

            # subprocess.run with check=True will raise CalledProcessError if the command returns non-zero.
            # We capture output to prevent it from cluttering logs unless there is an error.
            subprocess.run(check_cmd, check=True, capture_output=True)
            log.info(f"NAT rule for {cidr} already exists.")

        except FileNotFoundError:
            log.critical("The 'sudo' or 'iptables' command was not found. Is it installed and in the system's PATH?")
            # Stop processing further rules if iptables isn't available.
            break
        except subprocess.CalledProcessError:
            # This exception means the check command failed, which implies the rule does not exist.
            log.info(f"NAT rule for {cidr} not found. Attempting to add it.")
            try:
                add_cmd = ["sudo", "iptables", "-t", "nat", "-A", "POSTROUTING", "-s", cidr, "-j", "MASQUERADE"]
                log.debug(f"Adding NAT rule with command: {' '.join(add_cmd)}")
                subprocess.run(add_cmd, check=True, capture_output=True)
                log.info(f"Successfully added NAT rule for {cidr}.")
            except subprocess.CalledProcessError as add_error:
                log.error(f"Failed to add iptables NAT rule for {cidr}. Command failed with exit code {add_error.returncode}.")
                log.error(f"Stderr: {add_error.stderr.decode().strip()}")
            except FileNotFoundError:
                # This case is unlikely if the check command already ran, but included for robustness.
                log.critical("The 'sudo' or 'iptables' command was not found during rule addition.")
                break
