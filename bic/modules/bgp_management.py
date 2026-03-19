# ... (existing bgp_management.py content) ...

def create_client_frr_config(db_core: BIC_DB, client: dict):
    """Generates a client-side FRRouting (FRR) BGP configuration."""
    if not client.get("asn"):
        return None

    local_asn = db_core.find_one("settings", {"key": "bgp_local_asn"})["value"]
    client_asn = client["asn"]

    # Find our side of the WG tunnel to know the neighbor IP
    wg_server_p2p_ipv4_pool_id = db_core.find_one("ip_pools", {"name": "WG Server P2P IPv4"})["id"]
    wg_server_p2p_ipv6_pool_id = db_core.find_one("ip_pools", {"name": "WG Server P2P IPv6"})["id"]
    
    server_v4_ip = db_core.find_one("ip_allocations", {"pool_id": wg_server_p2p_ipv4_pool_id, "client_id": None})["ip_address"]
    server_v6_ip = db_core.find_one("ip_allocations", {"pool_id": wg_server_p2p_ipv6_pool_id, "client_id": None})["ip_address"]

    frr_conf = f"""!
! FRRouting BGP configuration for {client['name']}
! This should be adapted and placed in your /etc/frr/frr.conf
!
router bgp {client_asn}
 bgp router-id {client['name'].replace(' ', '_').lower()}.local
 !
 neighbor {server_v4_ip} remote-as {local_asn}
 neighbor {server_v4_ip} description BGP in the Cloud (IPv4)
 !
 neighbor {server_v6_ip} remote-as {local_asn}
 neighbor {server_v6_ip} description BGP in the Cloud (IPv6)
 !
 address-family ipv4 unicast
  network YOUR_PREFIX_HERE
 exit-address-family
 !
 address-family ipv6 unicast
  network YOUR_IPV6_PREFIX_HERE
 exit-address-family
!
"""
    return frr_conf

def create_client_bird_config(db_core: BIC_DB, client: dict):
    """Generates a client-side BIRD configuration."""
    if not client.get("asn"):
        return None

    local_asn = db_core.find_one("settings", {"key": "bgp_local_asn"})["value"]
    client_asn = client["asn"]

    wg_server_p2p_ipv4_pool_id = db_core.find_one("ip_pools", {"name": "WG Server P2P IPv4"})["id"]
    wg_server_p2p_ipv6_pool_id = db_core.find_one("ip_pools", {"name": "WG Server P2P IPv6"})["id"]
    
    server_v4_ip = db_core.find_one("ip_allocations", {"pool_id": wg_server_p2p_ipv4_pool_id, "client_id": None})["ip_address"]
    server_v6_ip = db_core.find_one("ip_allocations", {"pool_id": wg_server_p2p_ipv6_pool_id, "client_id": None})["ip_address"]

    bird_conf = f"""#
# Example BIRD configuration for {client['name']}
#

router id YOUR_ROUTER_ID; # e.g. 1.1.1.1

protocol device {{
    scan time 10;
}}

protocol kernel {{
    ipv4 {{ export all; }};
    ipv6 {{ export all; }};
}}

protocol static {{
    ipv4;
    route YOUR_PREFIX_HERE blackhole;
}}

protocol static {{
    ipv6;
    route YOUR_IPV6_PREFIX_HERE blackhole;
}}

protocol bgp v4_upstream {{
    local as {client_asn};
    neighbor {server_v4_ip} as {local_asn};
    source address YOUR_WG_IPV4_ADDRESS; # Your end of the WireGuard tunnel
    ipv4 {{
        import all;
        export where proto = "static";
    }};
}}

protocol bgp v6_upstream {{
    local as {client_asn};
    neighbor {server_v6_ip} as {local_asn};
    source address YOUR_WG_IPV6_ADDRESS; # Your end of the WireGuard tunnel
    ipv6 {{
        import all;
        export where proto = "static";
    }};
}}
"""
    return bird_conf

