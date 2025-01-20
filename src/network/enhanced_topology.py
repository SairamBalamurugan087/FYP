from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import TCLink
import random
import time

class EnhancedTopology(Topo):
    def build(self):
        # Create core switches (backbone of the network)
        core_switches = []
        for i in range(1, 4):
            switch = self.addSwitch(f'c{i}', cls=OVSSwitch, protocols='OpenFlow13')
            core_switches.append(switch)

        # Create distribution switches (intermediate layer)
        dist_switches = []
        for i in range(1, 7):
            switch = self.addSwitch(f'd{i}', cls=OVSSwitch, protocols='OpenFlow13')
            dist_switches.append(switch)

        # Create access switches (edge layer)
        access_switches = []
        for i in range(1, 13):
            switch = self.addSwitch(f'a{i}', cls=OVSSwitch, protocols='OpenFlow13')
            access_switches.append(switch)

        # Create hosts (multiple hosts per access switch)
        hosts = []
        for i in range(1, 37):  # 3 hosts per access switch
            host = self.addHost(f'h{i}')
            hosts.append(host)

        # Connect core switches to each other (full mesh)
        for i, switch1 in enumerate(core_switches):
            for switch2 in core_switches[i+1:]:
                self.addLink(switch1, switch2, cls=TCLink, bw=100)  # 100 Mbps links

        # Connect distribution switches to core switches
        for i, dist_switch in enumerate(dist_switches):
            # Each distribution switch connects to two core switches for redundancy
            core1 = core_switches[i % len(core_switches)]
            core2 = core_switches[(i + 1) % len(core_switches)]
            self.addLink(dist_switch, core1, cls=TCLink, bw=50)  # 50 Mbps links
            self.addLink(dist_switch, core2, cls=TCLink, bw=50)

        # Connect access switches to distribution switches
        for i, acc_switch in enumerate(access_switches):
            # Each access switch connects to two distribution switches
            dist1 = dist_switches[i % len(dist_switches)]
            dist2 = dist_switches[(i + 1) % len(dist_switches)]
            self.addLink(acc_switch, dist1, cls=TCLink, bw=25)  # 25 Mbps links
            self.addLink(acc_switch, dist2, cls=TCLink, bw=25)

        # Connect hosts to access switches
        for i, host in enumerate(hosts):
            # Connect each host to its access switch
            acc_switch = access_switches[i // 3]  # 3 hosts per access switch
            self.addLink(host, acc_switch, cls=TCLink, bw=10)  # 10 Mbps links

class NetworkSimulation:
    def __init__(self):
        self.net = None
        self.controller = None
        self.total_hosts = 36  # Total number of hosts in the network

    def start_network(self):
        """Initialize and start the network simulation."""
        topo = EnhancedTopology()
        self.controller = RemoteController('c0', ip='127.0.0.1', port=6633)
        self.net = Mininet(
            topo=topo,
            controller=self.controller,
            switch=OVSSwitch,
            link=TCLink,
            autoSetMacs=True,
            autoStaticArp=True
        )
        
        print("Starting network...")
        self.net.start()
        self._setup_network_conditions()
        
        print("Network is ready for simulation!")
        return self.net

    def _setup_network_conditions(self):
        """Set up initial network conditions and verify connectivity."""
        print("\nSetting up network conditions...")
        
        # Configure IP addresses for hosts
        for i, host in enumerate(self.net.hosts, 1):
            # Configure IP address
            host.cmd(f'ifconfig {host.name}-eth0 10.0.0.{i}/24')
            
            # Add default route
            host.cmd(f'route add default gw 10.0.0.254')
            
            # Set up host-specific configuration
            host.cmd('sysctl -w net.ipv4.tcp_congestion_control=cubic')
            host.cmd('sysctl -w net.ipv4.ip_forward=1')
        
        # Add random delay to links to simulate real network conditions
        for link in self.net.links:
            delay = random.randint(1, 5)
            link.intf1.config(delay=f'{delay}ms')
        
        # Wait for the network to initialize
        print("Waiting for network initialization...")
        time.sleep(5)
        
        # Verify basic connectivity
        self._verify_connectivity()

    def _verify_connectivity(self):
        """Verify network connectivity with detailed output."""
        print("\nVerifying network connectivity...")
        
        # Test connectivity between a subset of hosts
        test_hosts = random.sample(self.net.hosts, min(5, len(self.net.hosts)))
        
        for source in test_hosts:
            print(f"\nTesting connectivity from {source.name}:")
            for target in test_hosts:
                if source != target:
                    result = source.cmd(f'ping -c 1 -W 1 {target.IP()}')
                    success = '1 received' in result
                    print(f"{source.name} -> {target.name}: {'Success' if success else 'Failed'}")
                    
                    if not success:
                        print(f"Debug info for failed connection:")
                        print(f"Source ({source.name}) configuration:")
                        print(source.cmd('ifconfig'))
                        print(source.cmd('route -n'))
                        print(f"Target ({target.name}) configuration:")
                        print(target.cmd('ifconfig'))

    def verify_switch_flows(self):
        """Verify OpenFlow rules on all switches."""
        print("\nVerifying OpenFlow rules:")
        for switch in self.net.switches:
            print(f"\nSwitch {switch.name} flow rules:")
            print(switch.cmd('ovs-ofctl dump-flows ' + switch.name))
            print(f"Switch {switch.name} ports:")
            print(switch.cmd('ovs-ofctl show ' + switch.name))

    def simulate_traffic(self):
        """Generate sample traffic in the network."""
        print("\nSimulating network traffic...")
        
        # Select random hosts for servers and clients
        all_hosts = self.net.hosts
        server_hosts = random.sample(all_hosts, min(5, len(all_hosts)))
        client_hosts = [h for h in all_hosts if h not in server_hosts]
        
        # Start iperf servers
        for server in server_hosts:
            print(f"Starting iperf server on {server.name}")
            server.cmd('iperf -s &')
        
        # Start iperf clients
        for client in client_hosts[:5]:
            server = random.choice(server_hosts)
            print(f"Testing bandwidth from {client.name} to {server.name}")
            result = client.cmd(f'iperf -c {server.IP()} -t 10')
            print(f"Bandwidth test result: {result}")

        # Clean up iperf servers
        for server in server_hosts:
            server.cmd('kill %iperf')

    def monitor_network(self):
        """Monitor network statistics."""
        print("\nMonitoring network statistics...")
        
        for switch in self.net.switches:
            print(f"\nSwitch {switch.name} statistics:")
            print(switch.cmd('ovs-ofctl dump-ports ' + switch.name))
        
        for host in self.net.hosts:
            print(f"\nHost {host.name} statistics:")
            print(host.cmd('ifconfig'))

    def run_cli(self):
        """Start the Mininet CLI."""
        print("\nStarting Mininet CLI...")
        CLI(self.net)

    def stop_network(self):
        """Stop the network simulation."""
        if self.net:
            print("\nStopping network simulation...")
            # Clean up any remaining processes
            for host in self.net.hosts:
                host.cmd('kill %iperf')
            self.net.stop()

def main():
    """Main function to run the network simulation."""
    setLogLevel('info')
    
    simulation = NetworkSimulation()
    
    try:
        simulation.start_network()
        simulation.verify_switch_flows()
        simulation.simulate_traffic()
        simulation.monitor_network()
        simulation.run_cli()
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt. Stopping network simulation...")
    except Exception as e:
        print(f"\nError occurred: {e}")
    finally:
        simulation.stop_network()

if __name__ == '__main__':
    main()