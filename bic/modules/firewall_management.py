import subprocess
import ipaddress
from rich.console import Console
from bic.core import BIC_DB

CONSOLE = Console()
CHAIN_NAME = "BIC-SECURITY-FILTER"

def synchronize_firewall_rules(db_core: BIC_DB):
    """Generates and applies iptables rules for client port security."""
    CONSOLE.print(f"  -> Synchronizing firewall security chain ({CHAIN_NAME})...")

    try:
        # Ensure the chain exists and is in the FORWARD path
        _ensure_chain_exists()

        # Get a list of all current rules in our chain
        existing_rules = _get_existing_rules()

        # Determine the rules that SHOULD exist based on the database
        required_rules = _get_required_rules(db_core)

        # Compare and only apply if there's a difference
        if existing_rules != required_rules:
            CONSOLE.print("    -> Firewall changes detected, applying new ruleset...")
            _apply_new_ruleset(required_rules)
            CONSOLE.print("[green]✅ Firewall security rules synchronized.[/green]")
        else:
            CONSOLE.print("    -> Firewall is already up to date.")

    except Exception as e:
        CONSOLE.print(f"[bold red]Error synchronizing firewall rules: {e}[/bold red]")
        CONSOLE.print("[yellow]Please ensure 'iptables' and 'netfilter-persistent' are installed.[/yellow]")

def _ensure_chain_exists():
    """Creates the custom chain and links it to the FORWARD chain if needed."""
    # Check if chain exists
    subprocess.run(f"sudo iptables -L {CHAIN_NAME}", shell=True, check=False, capture_output=True)
    if subprocess.run(f"sudo iptables -L {CHAIN_NAME}", shell=True, check=False, capture_output=True).returncode != 0:
        subprocess.run(f"sudo iptables -N {CHAIN_NAME}", shell=True, check=True)

    # Check if rule exists in FORWARD chain
    if subprocess.run(f"sudo iptables -C FORWARD -j {CHAIN_NAME}", shell=True, check=False, capture_output=True).returncode != 0:
        subprocess.run(f"sudo iptables -A FORWARD -j {CHAIN_NAME}", shell=True, check=True)

def _get_existing_rules() -> list:
    """Returns a list of the rules currently in our custom chain."""
    rules_raw = subprocess.run(f"sudo iptables -S {CHAIN_NAME}", shell=True, check=True, capture_output=True, text=True).stdout
    return rules_raw.strip().split('\n') if rules_raw.strip() else []

def _get_required_rules(db_core: BIC_DB) -> list:
    """Constructs a list of rules that should be in the chain based on DB state."""
    rules = []
    smtp_allowed_ips = _get_smtp_allowed_ips(db_core)

    # Rule 1: Allow SMTP for authorized clients
    for ip in smtp_allowed_ips:
        rules.append(f"-A {CHAIN_NAME} -s {ip} -p tcp -m tcp --dport 25 -j ACCEPT")

    # Rule 2: Block SMTP for everyone else
    rules.append(f"-A {CHAIN_NAME} -p tcp -m tcp --dport 25 -j REJECT --reject-with tcp-reset")

    # Rule 3: Block other commonly attacked ports
    rules.append(f"-A {CHAIN_NAME} -p tcp -m multiport --dports 135,137,138,139,445,389,3268 -j REJECT --reject-with tcp-reset")
    rules.append(f"-A {CHAIN_NAME} -p udp -m multiport --dports 135,137,138,139,445,161,162,1900 -j REJECT")

    return rules

def _apply_new_ruleset(rules: list):
    """Flushes the chain and applies a new set of rules."""
    # Flush existing rules
    subprocess.run(f"sudo iptables -F {CHAIN_NAME}", shell=True, check=True)

    # Apply new rules
    for rule in rules:
        subprocess.run(f"sudo iptables {rule}", shell=True, check=True)
    
    # Persist the ruleset
    subprocess.run("sudo netfilter-persistent save", shell=True, check=True)

def _get_smtp_allowed_ips(db_core: BIC_DB) -> list:
    """Gets all public IPs and Subnets for clients with SMTP enabled."""
    allowed_clients = db_core.find_all_by("clients", {"allow_smtp": 1})
    if not allowed_clients:
        return []

    allowed_ips = []
    for client in allowed_clients:
        allocs = db_core.find_all_by('ip_allocations', {'client_id': client['id']})
        for alloc in allocs:
            if not ipaddress.ip_address(alloc['ip_address']).is_private:
                allowed_ips.append(alloc['ip_address'])
        
        subnets = db_core.find_all_by('ip_subnets', {'client_id': client['id']})
        for sub in subnets:
            if not ipaddress.ip_network(sub['subnet']).is_private:
                allowed_ips.append(sub['subnet'])
                
    return list(set(allowed_ips))

def setup_nat_rules():
    """Ensures a NAT rule exists for the 172.30.0.0/16 private range."""
    CONSOLE.print("  -> Ensuring NAT rules for private ranges...")
    nat_rule = "-s 172.30.0.0/16 -j MASQUERADE"
    
    try:
        # Check if the rule already exists in the POSTROUTING chain of the nat table
        check_command = f"sudo iptables -t nat -C POSTROUTING {nat_rule}"
        if subprocess.run(check_command, shell=True, check=False, capture_output=True).returncode != 0:
            # Rule doesn't exist, so we add it
            add_command = f"sudo iptables -t nat -A POSTROUTING {nat_rule}"
            subprocess.run(add_command, shell=True, check=True)
            CONSOLE.print("    -> Added NAT rule for 172.30.0.0/16.")
            # Persist the ruleset
            subprocess.run("sudo netfilter-persistent save", shell=True, check=True)
        else:
            CONSOLE.print("    -> NAT rule for 172.30.0.0/16 already exists.")

    except Exception as e:
        CONSOLE.print(f"[bold red]Error setting up NAT rules: {e}[/bold red]")
