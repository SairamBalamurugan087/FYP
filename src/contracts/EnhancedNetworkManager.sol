// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract EnhancedNetworkManager {
    enum SwitchType { CORE, DISTRIBUTION, ACCESS }
    enum LinkState { ACTIVE, DEGRADED, FAILED }
    
    struct Switch {
        string switchId;
        SwitchType switchType;
        bool isActive;
        uint256 totalPorts;
        uint256 usedPorts;
    }
    
    struct Link {
        string sourceId;
        string destId;
        uint256 bandwidth;
        uint256 currentLoad;
        uint256 latency;
        LinkState state;
        uint256 lastUpdated;
    }
    
    struct PathRedundancy {
        string primaryPath;    // Comma-separated switch IDs
        string secondaryPath;  // Backup path
        bool isPrimaryActive;
        uint256 lastFailover;
    }
    
    // State variables
    mapping(string => Switch) public switches;
    mapping(bytes32 => Link) public links;
    mapping(bytes32 => PathRedundancy) public redundantPaths;
    address public owner;
    
    // Events
    event SwitchStatusChanged(string switchId, bool isActive);
    event LinkStateChanged(string sourceId, string destId, LinkState state);
    event PathFailover(bytes32 pathId, bool isPrimaryActive);
    event MetricsUpdated(string switchId, uint256 load, uint256 timestamp);

    constructor() {
        owner = msg.sender;
        require(owner != address(0), "Invalid owner address");
    }
    
    // Switch management
    function registerSwitch(
    string memory switchId,
    SwitchType switchType,
    uint256 totalPorts
    ) public {
        require(bytes(switchId).length > 0, "Switch ID cannot be empty");
        require(totalPorts > 0, "Total ports must be greater than 0");
        require(uint8(switchType) <= uint8(SwitchType.ACCESS), "Invalid switch type");
    
        switches[switchId] = Switch(
            switchId,
            switchType,
            true,
            totalPorts,
            0
        );
    }
    
    // Link management
    function updateLink(
        string memory sourceId,
        string memory destId,
        uint256 bandwidth,
        uint256 latency,
        LinkState state
    ) public {
        bytes32 linkId = keccak256(abi.encodePacked(sourceId, destId));
        links[linkId] = Link(
            sourceId,
            destId,
            bandwidth,
            0,
            latency,
            state,
            block.timestamp
        );
        
        emit LinkStateChanged(sourceId, destId, state);
    }
    
    // Path redundancy management
    function setRedundantPath(
        string memory sourceId,
        string memory destId,
        string memory primaryPath,
        string memory secondaryPath
    ) public {
        bytes32 pathId = keccak256(abi.encodePacked(sourceId, destId));
        redundantPaths[pathId] = PathRedundancy(
            primaryPath,
            secondaryPath,
            true,
            0
        );
    }
    
    function triggerFailover(string memory sourceId, string memory destId) public {
        bytes32 pathId = keccak256(abi.encodePacked(sourceId, destId));
        PathRedundancy storage path = redundantPaths[pathId];
        path.isPrimaryActive = !path.isPrimaryActive;
        path.lastFailover = block.timestamp;
        
        emit PathFailover(pathId, path.isPrimaryActive);
    }
    
    // Metrics and monitoring
    function updateMetrics(
        string memory switchId,
        uint256 currentLoad,
        uint256 linkLatency
    ) public {
        Switch storage switch_ = switches[switchId];
        require(switch_.isActive, "Switch is not active");
        
        // Update link metrics
        bytes32 linkId = keccak256(abi.encodePacked(switchId));
        Link storage link = links[linkId];
        link.currentLoad = currentLoad;
        link.latency = linkLatency;
        link.lastUpdated = block.timestamp;
        
        emit MetricsUpdated(switchId, currentLoad, block.timestamp);
    }
    
    // Getters for network state
    function getLinkStatus(string memory sourceId, string memory destId) 
        public view returns (Link memory) {
        bytes32 linkId = keccak256(abi.encodePacked(sourceId, destId));
        return links[linkId];
    }
    
    function getRedundantPath(string memory sourceId, string memory destId) 
        public view returns (PathRedundancy memory) {
        bytes32 pathId = keccak256(abi.encodePacked(sourceId, destId));
        return redundantPaths[pathId];
    }
}