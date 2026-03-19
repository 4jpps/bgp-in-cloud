import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add the project root to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bic.webapp import app

@pytest.fixture(scope="module")
def client():
    # The TestClient will manage the app's lifespan
    with TestClient(app) as c:
        yield c

def test_read_main_dashboard(client):
    """Test that the main dashboard loads without errors."""
    response = client.get("/")
    assert response.status_code == 200
    assert "System Status" in response.text

def test_list_clients_page(client):
    """Test that the client list page loads without errors."""
    response = client.get("/page/clients/list")
    assert response.status_code == 200
    assert "List Clients" in response.text

def test_list_pools_page(client):
    """Test that the IP Pools list page loads without errors."""
    response = client.get("/page/network/pools/list")
    assert response.status_code == 200
    assert "List IP Pools" in response.text

def test_system_settings_page(client):
    """Test that the system settings page loads without errors."""
    response = client.get("/page/system/settings")
    assert response.status_code == 200
    assert "System Settings" in response.text

def test_system_statistics_page(client):
    """Test that the system statistics page loads without errors."""
    response = client.get("/system/statistics")
    assert response.status_code == 200
    assert "System Statistics" in response.text

# You can add more tests here for other pages and API endpoints.
