# src/dashboard/app.py
from flask import Flask, render_template, jsonify, request
from web3 import Web3
import json
from datetime import datetime
from typing import Dict, List
import threading
import time
from src.controller.enhanced_sdn_controller import EnhancedOpenDaylightController, SwitchType

app = Flask(__name__)

# Initialize Web3 and contract
w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
with open('build/contracts/EnhancedNetworkManager.json') as f:
    contract_json = json.load(f)
contract_address = '0xCFFb65E9e2688B1E7F925843e6FE4d3fF152A446'  # Deploy contract and put address here
contract = w3.eth.contract(address=contract_address, abi=contract_json['abi'])

# Initialize OpenDaylight controller
sdn_controller = EnhancedOpenDaylightController()

# Cache for network metrics
metrics_cache = {
    'switches': {},
    'links': {},
    'paths': {},
    'layer_stats': {}
}

def update_metrics_cache():
    """Background task to update metrics cache"""
    while True:
        try:
            # Update switch metrics
            topology = sdn_controller.get_topology(force_refresh=True)
            for switch_id in topology.get('switches', []):
                switch_type = sdn_controller.get_switch_type(switch_id)
                metrics = contract.functions.getMetrics(switch_id).call()
                metrics_cache['switches'][switch_id] = {
                    'type': switch_type.value,
                    'load': metrics['currentLoad'],
                    'status': metrics['isActive'],
                    'last_updated': datetime.now().isoformat()
                }

            # Update link metrics
            for link in topology.get('links', []):
                link_id = f"{link['source']}_{link['target']}"
                link_metrics = sdn_controller.monitor_link_metrics(link_id)
                metrics_cache['links'][link_id] = {
                    'bandwidth': link_metrics.get('bytes_transmitted', 0),
                    'latency': link_metrics.get('latency', 0),
                    'status': link_metrics.get('status', 'active'),
                    'last_updated': datetime.now().isoformat()
                }

            # Update layer statistics
            for layer in SwitchType:
                layer_stats = sdn_controller.get_layer_statistics(layer)
                metrics_cache['layer_stats'][layer.value] = layer_stats

        except Exception as e:
            print(f"Error updating metrics: {e}")
        
        time.sleep(5)  # Update every 5 seconds

# Start metrics update thread
metrics_thread = threading.Thread(target=update_metrics_cache, daemon=True)
metrics_thread.start()

@app.route('/')
def index():
    """Render main dashboard page"""
    return render_template('src/templates/index.html')

@app.route('/api/topology')
def get_topology():
    """Get current network topology"""
    topology = sdn_controller.get_topology()
    return jsonify({
        'nodes': topology.get('nodes', []),
        'links': topology.get('links', []),
        'layers': {
            'core': [n for n in topology.get('nodes', []) if n['id'].startswith('c')],
            'distribution': [n for n in topology.get('nodes', []) if n['id'].startswith('d')],
            'access': [n for n in topology.get('nodes', []) if n['id'].startswith('a')]
        }
    })

@app.route('/api/metrics')
def get_metrics():
    """Get current network metrics"""
    return jsonify(metrics_cache)

@app.route('/api/layer/<layer>')
def get_layer_metrics(layer):
    """Get metrics for specific network layer"""
    return jsonify(metrics_cache['layer_stats'].get(layer, {}))

@app.route('/api/switch/<switch_id>')
def get_switch_metrics(switch_id):
    """Get metrics for specific switch"""
    return jsonify(metrics_cache['switches'].get(switch_id, {}))

@app.route('/api/link/<source>/<target>')
def get_link_metrics(source, target):
    """Get metrics for specific link"""
    link_id = f"{source}_{target}"
    return jsonify(metrics_cache['links'].get(link_id, {}))

@app.route('/api/path/redundant', methods=['POST'])
def configure_redundant_path():
    """Configure redundant path between two points"""
    data = request.json
    success = sdn_controller.setup_redundant_path(
        data['source'],
        data['destination'],
        data['primary_path'],
        data['backup_path']
    )
    return jsonify({'success': success})

@app.route('/api/alerts')
def get_alerts():
    """Get network alerts and warnings"""
    alerts = []
    
    # Check switch status
    for switch_id, metrics in metrics_cache['switches'].items():
        if not metrics['status']:
            alerts.append({
                'level': 'critical',
                'message': f'Switch {switch_id} is down',
                'timestamp': datetime.now().isoformat()
            })
        elif metrics['load'] > 80:
            alerts.append({
                'level': 'warning',
                'message': f'High load on switch {switch_id}: {metrics["load"]}%',
                'timestamp': datetime.now().isoformat()
            })

    # Check link status
    for link_id, metrics in metrics_cache['links'].items():
        if metrics['status'] != 'active':
            alerts.append({
                'level': 'critical',
                'message': f'Link {link_id} is {metrics["status"]}',
                'timestamp': datetime.now().isoformat()
            })

    return jsonify(alerts)

if __name__ == '__main__':
    app.run(debug=True)