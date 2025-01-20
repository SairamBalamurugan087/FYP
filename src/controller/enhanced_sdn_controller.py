from typing import Dict, List, Tuple
import requests
import json
import time
from enum import Enum

class SwitchType(Enum):
    CORE = "core"
    DISTRIBUTION = "distribution"
    ACCESS = "access"

class EnhancedOpenDaylightController:
    def __init__(self, host: str = "localhost", port: int = 8181):
        self.base_url = f"http://{host}:{port}/restconf"
        self.auth = ("admin", "admin")
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        self.topology_cache = {}
        self.last_cache_update = 0
        self.cache_timeout = 30  # seconds

    def get_topology(self, force_refresh: bool = False) -> Dict:
        """Fetch network topology with caching."""
        current_time = time.time()
        if force_refresh or (current_time - self.last_cache_update) > self.cache_timeout:
            url = f"{self.base_url}/operational/network-topology:network-topology"
            response = requests.get(url, auth=self.auth, headers=self.headers)
            self.topology_cache = response.json()
            self.last_cache_update = current_time
        return self.topology_cache

    def get_switch_type(self, switch_id: str) -> SwitchType:
        """Determine switch type based on ID prefix."""
        if switch_id.startswith('c'):
            return SwitchType.CORE
        elif switch_id.startswith('d'):
            return SwitchType.DISTRIBUTION
        else:
            return SwitchType.ACCESS

    def install_layer_specific_flow(self, switch_id: str, flow_config: Dict) -> bool:
        """Install flow rules with layer-specific considerations."""
        switch_type = self.get_switch_type(switch_id)
        
        # Modify flow rules based on switch layer
        if switch_type == SwitchType.CORE:
            flow_config["priority"] = 100  # Highest priority for core
            flow_config["idle-timeout"] = 0  # Permanent flows
        elif switch_type == SwitchType.DISTRIBUTION:
            flow_config["priority"] = 50
            flow_config["idle-timeout"] = 300  # 5 minutes
        else:  # ACCESS
            flow_config["priority"] = 10
            flow_config["idle-timeout"] = 60  # 1 minute

        url = f"{self.base_url}/config/opendaylight-inventory:nodes/node/{switch_id}/flow-node-inventory:table/0/flow/{flow_config['id']}"
        response = requests.put(url, auth=self.auth, headers=self.headers, json=flow_config)
        return response.status_code == 200

    def setup_redundant_path(
        self, 
        source: str, 
        destination: str, 
        primary_path: List[str], 
        backup_path: List[str]
    ) -> Tuple[bool, bool]:
        """Configure both primary and backup paths."""
        primary_success = self.update_route(source, destination, primary_path, is_primary=True)
        backup_success = self.update_route(source, destination, backup_path, is_primary=False)
        return primary_success, backup_success

    def update_route(
        self, 
        source: str, 
        destination: str, 
        path: List[str], 
        is_primary: bool = True
    ) -> bool:
        """Update routing with support for primary/backup paths."""
        flow_configs = self._generate_enhanced_flow_configs(
            source, destination, path, is_primary
        )
        
        success = True
        for node_id, flow_config in flow_configs.items():
            if not self.install_layer_specific_flow(node_id, flow_config):
                success = False
                break
        return success

    def _generate_enhanced_flow_configs(
        self, 
        source: str, 
        destination: str, 
        path: List[str], 
        is_primary: bool
    ) -> Dict:
        """Generate enhanced flow configurations for each node."""
        configs = {}
        priority_base = 1000 if is_primary else 500
        
        for i, node_id in enumerate(path):
            if i < len(path) - 1:
                next_hop = path[i + 1]
                switch_type = self.get_switch_type(node_id)
                
                # Adjust priority based on switch type
                type_priority = {
                    SwitchType.CORE: 200,
                    SwitchType.DISTRIBUTION: 100,
                    SwitchType.ACCESS: 50
                }[switch_type]
                
                configs[node_id] = {
                    "id": f"flow_{source}_{destination}_{i}_{'primary' if is_primary else 'backup'}",
                    "priority": priority_base + type_priority,
                    "match": {
                        "ethernet-match": {
                            "ethernet-type": {"type": 2048}
                        },
                        "ipv4-destination": destination + "/32"
                    },
                    "instructions": {
                        "instruction": [{
                            "order": 0,
                            "apply-actions": {
                                "action": [{
                                    "order": 0,
                                    "output-action": {
                                        "output-node-connector": next_hop
                                    }
                                }]
                            }
                        }]
                    }
                }
        return configs

    def monitor_link_metrics(self, link_id: str) -> Dict:
        """Monitor link performance metrics."""
        url = f"{self.base_url}/operational/opendaylight-inventory:nodes/node/{link_id}/node-connector-statistics"
        response = requests.get(url, auth=self.auth, headers=self.headers)
        if response.status_code == 200:
            stats = response.json()
            return {
                "bytes_received": stats.get("bytes-received", 0),
                "bytes_transmitted": stats.get("bytes-transmitted", 0),
                "packets_received": stats.get("packets-received", 0),
                "packets_transmitted": stats.get("packets-transmitted", 0),
                "timestamp": time.time()
            }
        return {}

    def get_layer_statistics(self, layer: SwitchType) -> Dict:
        """Get statistics for a specific network layer."""
        topology = self.get_topology()
        layer_stats = {
            "total_switches": 0,
            "active_switches": 0,
            "total_links": 0,
            "active_links": 0,
            "average_load": 0
        }
        
        # Process topology data to gather layer-specific statistics
        # Implementation details would depend on topology data structure
        
        return layer_stats