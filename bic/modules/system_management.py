import subprocess
import ipaddress
import os
from rich.console import Console
from bic.core import BIC_DB
from bic.modules import bird_management # New Import

CHAIN_NAME = "BIC-NAT-MASQUERADE"
SYSCTL_CONF_FILE = "/etc/sysctl.d/99-bic-forwarding.conf"

def setup_host_networking(db_core: BIC_DB):
    console = Console()
    console.print("\n[cyan]Verifying host network configuration...[/cyan]")
    
    forwarding_changed = _enable_ip_forwarding()
    nat_changed = synchronize_nat_rules(db_core)
    
    # Synchronize all BIRD configurations
    bird_management.synchronize_bird_prefix_filters(db_core)
    bird_management.reload_bird_config()

    if forwarding_changed:
        console.print("  -> Applying IP forwarding rules...")
        try:
            subprocess.run(["sudo", "sysctl", "-p", SYSCTL_CONF_FILE], check=True, capture_output=True)
            console.print("[green]✅ IP forwarding enabled.[/green]")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            console.print(f"[bold red]Error applying sysctl settings: {e}[/bold red]")
            
    if not forwarding_changed and not nat_changed:
        console.print("[green]✅ Host networking is already up to date.[/green]")


def _enable_ip_forwarding():
    console = Console()
    config_content = "# Managed by BIC IPAM\nnet.ipv4.ip_forward=1\nnet.ipv6.conf.all.forwarding=1\n"
    
    if os.path.exists(SYSCTL_CONF_FILE):
        try:
            with open(SYSCTL_CONF_FILE, 'r') as f:
                if f.read() == config_content:
                    return False
        except IOError:
             pass # Handle case where file is not readable

    console.print(f"  -> Writing IP forwarding config to {SYSCTL_CONF_FILE}...")
    try:
        temp_file_path = "/tmp/99-bic-forwarding.tmp"
        with open(temp_file_path, "w") as f:
            f.write(config_content)
        
        subprocess.run(["sudo", "mv", temp_file_path, SYSCTL_CONF_FILE], check=True)
        subprocess.run(["sudo", "chown", "root:root", SYSCTL_CONF_FILE], check=True)
        return True
    except (IOError, subprocess.CalledProcessError) as e:
        console.print(f"[bold red]Error writing sysctl config: {e}[/bold red]")
        return False

def synchronize_nat_rules(db_core: BIC_DB):
    console = Console()
    try:
        route_cmd = "ip -o -4 route show to default"
        proc = subprocess.run(route_cmd, shell=True, check=True, capture_output=True, text=True)
        iface = proc.stdout.split()[4]

        current_rules_cmd = f"sudo iptables-save -t nat | grep -- '-A {CHAIN_NAME}' || true"
        proc = subprocess.run(current_rules_cmd, shell=True, check=True, capture_output=True, text=True)
        existing_rules = proc.stdout.strip().split('\n')
        
        required_rules = []
        pools = db_core.find_all("ip_pools")
        for pool in pools:
            try:
                network = ipaddress.ip_network(pool['cidr'])
                if network.is_private:
                    required_rules.append(f"-A {CHAIN_NAME} -s {pool['cidr']} -o {iface} -j MASQUERADE")
            except ValueError:
                continue

        if sorted(existing_rules) == sorted(required_rules):
            return False

        console.print("  -> Updating NAT firewall rules...")
        subprocess.run(f"sudo iptables -t nat -F {CHAIN_NAME}", shell=True, capture_output=True)
        subprocess.run(f"sudo iptables -t nat -D POSTROUTING -j {CHAIN_NAME}", shell=True, capture_output=True)
        subprocess.run(f"sudo iptables -t nat -X {CHAIN_NAME}", shell=True, capture_output=True)

        subprocess.run(f"sudo iptables -t nat -N {CHAIN_NAME}", shell=True, check=True, capture_output=True)
        subprocess.run(f"sudo iptables -t nat -A POSTROUTING -j {CHAIN_NAME}", shell=True, check=True, capture_output=True)

        for rule_args in required_rules:
            if not rule_args: continue
            console.print(f"    -> Adding NAT for private range: {rule_args.split()[3]}")
            subprocess.run(f"sudo iptables -t nat {rule_args}", shell=True, check=True, capture_output=True)

        subprocess.run("sudo netfilter-persistent save", shell=True, check=True, capture_output=True)
        console.print("[green]✅ NAT rules updated and saved.[/green]")
        return True

    except FileNotFoundError:
        console.print("[bold yellow]Warning: 'iptables' or 'netfilter-persistent' not found. Skipping NAT setup.[/bold yellow]")
        return False
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error synchronizing NAT rules:[/bold red]")
        console.print(f"[red]COMMAND: {e.cmd}[/red]")
        console.print(f"[red]STDERR: {e.stderr.decode() if e.stderr else 'N/A'}[/red]")
        return False
