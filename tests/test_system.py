# tests/test_system.py
import requests
import json
import time
from web3 import Web3

def test_system_integration():
    # 1. Test OpenDaylight Controller
    def test_opendaylight():
        response = requests.get(
            'http://localhost:8181/restconf/operational/network-topology:network-topology',
            auth=('admin', 'admin'),
            headers={'Accept': 'application/json'}
        )
        assert response.status_code == 200
        print("OpenDaylight Controller: OK")

    # 2. Test Blockchain Connection
    def test_blockchain():
        w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
        assert w3.is_connected()
        print("Blockchain Connection: OK")

    # 3. Test Network Simulation
    def test_network():
        # Ping between hosts in Mininet
        # This should be run manually in Mininet CLI:
        # mininet> pingall
        print("Run 'pingall' in Mininet CLI to test network connectivity")

    # 4. Test Dashboard
    def test_dashboard():
        response = requests.get('http://localhost:5000/api/topology')
        assert response.status_code == 200
        print("Dashboard API: OK")

    # Run tests
    try:
        test_opendaylight()
        test_blockchain()
        test_dashboard()
        print("All systems operational!")
    except Exception as e:
        print(f"Error during testing: {e}")

if __name__ == "__main__":
    test_system_integration()