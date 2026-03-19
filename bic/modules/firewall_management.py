import subprocess
from rich.console import Console

CONSOLE = Console()

# Define the private ranges that need NAT
PRIVATE_RANGES = ["172.30.0.0/16"]

def ensure_nat_rules():
    """Ensures that the necessary iptables NAT rules for private ranges exist."""
    for cidr in PRIVATE_RANGES:
        try:
            # Check if the rule already exists
            check_cmd = f"sudo iptables -t nat -C POSTROUTING -s {cidr} -j MASQUERADE"
            proc_check = subprocess.run(check_cmd, shell=True, check=False, capture_output=True)

            # If the check command fails (returns non-zero), the rule doesn't exist
            if proc_check.returncode != 0:
                CONSOLE.print(f"  -> NAT rule for {cidr} not found. Adding it...")
                add_cmd = f"sudo iptables -t nat -A POSTROUTING -s {cidr} -j MASQUERADE"
                subprocess.run(add_cmd, shell=True, check=True)
                CONSOLE.print(f"[green]  -> Successfully added NAT rule for {cidr}.[/green]")
            else:
                CONSOLE.print(f"  -> NAT rule for {cidr} already exists.")

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            CONSOLE.print(f"[bold red]Error managing iptables NAT rule for {cidr}: {e}[/bold red]")
            CONSOLE.print("[bold yellow]Please ensure iptables is installed and you have sudo privileges.[/bold yellow]")
