import pytest
import os
import sys
import uuid
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Add the project root to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bic.core import BIC_DB
from bic.webapp import app, get_db
from bic.modules import network_management, client_management, wireguard_management, bgp_management

# --- Test Setup and Fixtures ---

@pytest.fixture(scope="function")
def db_session():
    """Creates a temporary, in-memory SQLite database for a test function."""
    # Using a file-based memory DB is more stable for multi-threading tests if needed
    db = BIC_DB(db_path=":memory:")
    yield db

@pytest.fixture(scope="function")
def client(db_session):
    """Creates a TestClient for the FastAPI app that uses the in-memory DB."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# --- Unit Tests for Business Logic (modules) ---

def test_add_and_get_next_ip(db_session):
    """Tests adding a pool and then allocating the next available IP."""
    pool_id = network_management.add_pool(db_session, "Test Pool", "192.168.10.0/29", "A test pool")
    assert pool_id is not None

    # Create a dummy client with an explicit ID
    client_id = str(uuid.uuid4())
    db_session.insert("clients", {"id": client_id, "name": "dummy", "type": "Standard"})

    ip1 = network_management.get_next_available_ip_in_pool(db_session, pool_id)
    assert ip1 == "192.168.10.1"

    # Manually insert an allocation to simulate that ip1 is taken
    alloc_id = str(uuid.uuid4())
    insert_result = db_session.insert("ip_allocations", {"id": alloc_id, "pool_id": pool_id, "address": ip1, "client_id": client_id})
    assert insert_result is not None

    ip2 = network_management.get_next_available_ip_in_pool(db_session, pool_id)
    assert ip2 == "192.168.10.2"

def test_allocate_subnet(db_session):
    """Tests allocating a subnet from a larger pool."""
    pool_id = network_management.add_pool(db_session, "Subnet Test Pool", "10.0.0.0/16", "A test pool")
    client_id = str(uuid.uuid4())
    db_session.insert("clients", {"id": client_id, "name": "dummy", "type": "Standard"})

    subnet_alloc_id = network_management.allocate_next_available_subnet(db_session, pool_id, 24, client_id, "test subnet")
    assert subnet_alloc_id is not None

    allocation = db_session.find_one("ip_allocations", {"id": subnet_alloc_id})
    assert allocation is not None
    assert allocation['address'] == "10.0.0.0/24"

@patch('bic.modules.wireguard_management.subprocess.run')
@patch('bic.modules.bgp_management.subprocess.run')
def test_provision_and_deprovision_client(mock_bgp_run, mock_wg_run, db_session):
    """Tests the full lifecycle of provisioning and deprovisioning a client."""
    # 1. Setup
    pool_id = network_management.add_pool(db_session, "Main Pool", "172.16.0.0/16", "main")
    # Insert a complete server_interfaces record with an ID
    server_interface_id = str(uuid.uuid4())
    db_session.insert("server_interfaces", {
        'id': server_interface_id,
        'name': 'wg0',
        'address': '172.16.0.1/16',
        'listen_port': 51820,
        'private_key': 'dummy_server_private_key',
        'public_key': 'dummy_server_public_key'
    })
    
    # Mock the wg command-line tools
    def wg_side_effect(*args, **kwargs):
        if args[0] == ['wg', 'genkey']:
            return MagicMock(stdout='dummy_client_private_key', strip=lambda: 'dummy_client_private_key', check_returncode=lambda: None)
        if args[0] == ['wg', 'pubkey']:
            return MagicMock(stdout='dummy_client_public_key', strip=lambda: 'dummy_client_public_key', check_returncode=lambda: None)
        return MagicMock() # Default mock for other calls
    mock_wg_run.side_effect = wg_side_effect

    # 2. Provision a new client
    client_id = client_management.provision_new_client(
        db_core=db_session,
        name="Test Client",
        email="test@example.com",
        type="Standard"
    )
    assert client_id is not None

    # 3. Assign an IP to the client
    client_management.update_client_details(
        db_core=db_session,
        client_id=client_id,
        name="Test Client Updated", # Change name to test update
        email="test@example.com",
        type="Standard",
        **{'assignment_pool_id[]': [str(pool_id)], 'assignment_type[]': ['static']}
    )

    # 4. Verify resources were created
    client_obj = db_session.find_one("clients", {"id": client_id})
    assert client_obj['name'] == "Test Client Updated"
    
    allocation = db_session.find_one("ip_allocations", {"client_id": client_id})
    assert allocation is not None
    assert allocation['address'] == "172.16.0.2"

    peer = db_session.find_one("wireguard_peers", {"client_id": client_id})
    assert peer is not None
    assert allocation['address'] in peer['allowed_ips']

    # 5. Deprovision the client
    client_management.deprovision_and_delete_client(db_session, client_id)

    # 6. Verify resources were deleted
    assert db_session.find_one("clients", {"id": client_id}) is None
    assert db_session.find_one("ip_allocations", {"client_id": client_id}) is None
    assert db_session.find_one("wireguard_peers", {"client_id": client_id}) is None

# --- Integration Tests for Web App (API/UI) ---

def test_read_dashboard(client):
    """Tests that the main dashboard page loads correctly."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Dashboard" in response.text

def test_api_and_page_lifecycles(client):
    """Tests the full lifecycle of creating and deleting items via the web UI pages."""
    # 1. Add an IP Pool
    response = client.post("/action/network/pools/add", data={"name": "Web Test Pool", "cidr": "10.10.0.0/16", "description": "web"}, follow_redirects=False)
    assert response.status_code == 303 # Check for redirect
    
    # Follow the redirect
    response = client.get(response.headers['location'])
    assert response.status_code == 200
    assert "Web Test Pool" in response.text

    # 2. Provision a client
    response = client.post("/action/clients/provision", data={"name": "Web Client", "email": "web@test.com", "type": "Standard"}, follow_redirects=False)
    assert response.status_code == 303

    # Verify by listing clients
    response = client.get("/page/clients/list")
    assert response.status_code == 200
    assert "Web Client" in response.text

    # Find the new client's ID. This is a bit fragile but works for this test.
    db = app.dependency_overrides[get_db]()
    client_obj = db.find_one("clients", {"name": "Web Client"})
    assert client_obj is not None
    client_id = client_obj['id']

    # 3. Delete the client
    response = client.post(f"/action/clients/delete/{client_id}", data={"id": client_id}, follow_redirects=False)
    assert response.status_code == 303
    
    # Verify client is gone by following redirect
    response = client.get(response.headers['location'])
    assert "Web Client" not in response.text
