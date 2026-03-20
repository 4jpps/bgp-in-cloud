#!/usr/bin/env python
"""
This file defines the UI structure for the BGP Management section.
"""

from bic.ui.schema import UIMenu, UIMenuItem, UIView, UIAction, FormField, TableColumn
from bic.modules import bgp_management
from bic.modules.wireguard_management import get_wireguard_peers_for_dropdown

list_bgp_peers_view = UIView(
    name="List BGP Peers",
    template="bgp_peer_list.html",
    handler=bgp_management.list_bgp_peers,
    table_columns=[
        TableColumn(name="name", label="Name"),
        TableColumn(name="hostname", label="Hostname"),
        TableColumn(name="asn", label="ASN"),
        TableColumn(name="enabled", label="Enabled"),
        TableColumn(name="wireguard_tunnel", label="WireGuard Tunnel"),
    ]
)

add_bgp_peer_action = UIAction(
    name="Add BGP Peer",
    handler=bgp_management.create_bgp_peer,
    redirect_to="/page/bgp/list",
    template="bgp_peer_form.html",
    form_fields=[
        FormField(name="name", label="Name", required=True),
        FormField(name="hostname", label="Hostname", required=True),
        FormField(name="asn", label="ASN", type="number", required=True),
        FormField(name="enabled", label="Enabled", type="checkbox"),
        FormField(name="wireguard_tunnel_id", label="WireGuard Tunnel", type="select", options_loader=get_wireguard_peers_for_dropdown, help_text="Optional: Associate with an existing WireGuard peer."),
    ]
)

edit_bgp_peer_action = UIAction(
    name="Edit BGP Peer",
    handler=bgp_management.update_bgp_peer,
    redirect_to="/page/bgp/list",
    template="bgp_peer_form.html",
    loader=bgp_management.get_bgp_peer,
    form_fields=[
        FormField(name="name", label="Name", required=True),
        FormField(name="hostname", label="Hostname", required=True),
        FormField(name="asn", label="ASN", type="number", required=True),
        FormField(name="enabled", label="Enabled", type="checkbox"),
        FormField(name="wireguard_tunnel_id", label="WireGuard Tunnel", type="select", options_loader=get_wireguard_peers_for_dropdown, help_text="Optional: Associate with an existing WireGuard peer."),
    ]
)

delete_bgp_peer_action = UIAction(
    name="Delete BGP Peer",
    handler=bgp_management.delete_bgp_peer,
    redirect_to="/page/bgp/list",
    form_fields=[]
)

bgp_status_dashboard_view = UIView(
    name="BGP Status Dashboard",
    template="bgp_status_dashboard.html",
    handler=bgp_management.get_bgp_summary,
)

manage_peer_prefixes_view = UIView(
    name="Manage BGP Prefixes",
    template="bgp_prefix_list.html",
    handler=bgp_management.list_advertised_prefixes,
    loader=bgp_management.get_bgp_peer, # To get the peer's name for the title
)

add_prefix_action = UIAction(
    name="Add Prefix",
    handler=bgp_management.add_advertised_prefix,
    redirect_to="/page/bgp/prefixes/manage/{peer_id}",
    form_fields=[
        FormField(name="prefix", label="Prefix", required=True),
    ]
)

delete_prefix_action = UIAction(
    name="Delete Prefix",
    handler=bgp_management.delete_advertised_prefix,
    # The redirect will be handled by the referer header
    form_fields=[]
)

toggle_blackhole_action = UIAction(
    name="Toggle Blackhole",
    handler=bgp_management.toggle_blackhole_prefix,
    # The redirect will be handled by the referer header
    form_fields=[]
)

all_prefixes_view = UIView(
    name="All Advertised Prefixes",
    template="all_prefixes.html",
    handler=bgp_management.list_all_advertised_prefixes,
)

bgp_menu = UIMenu(
    name="BGP Management",
    items=[
        UIMenuItem(name="Status Dashboard", path="status", item=bgp_status_dashboard_view),
        UIMenuItem(name="All Prefixes", path="all-prefixes", item=all_prefixes_view),
        UIMenuItem(name="List Peers", path="list", item=list_bgp_peers_view),
        UIMenuItem(name="Add Peer", path="add", item=add_bgp_peer_action),
        UIMenuItem(name="Edit Peer", path="edit/{id}", item=edit_bgp_peer_action, hidden=True),
        UIMenuItem(name="Delete Peer", path="delete/{id}", item=delete_bgp_peer_action, hidden=True),
        UIMenuItem(name="Manage Prefixes", path="prefixes/manage/{peer_id}", item=manage_peer_prefixes_view, hidden=True),
        UIMenuItem(name="Add Prefix", path="prefixes/add/{peer_id}", item=add_prefix_action, hidden=True),
        UIMenuItem(name="Delete Prefix", path="prefixes/delete/{id}", item=delete_prefix_action, hidden=True),
        UIMenuItem(name="Toggle Blackhole", path="prefixes/blackhole/{id}", item=toggle_blackhole_action, hidden=True),
    ]
)
