const EnhancedNetworkManager = artifacts.require("EnhancedNetworkManager");

module.exports = function(deployer, network, accounts) {
  deployer.then(async () => {
    try {
      // Deploy the EnhancedNetworkManager contract
      await deployer.deploy(EnhancedNetworkManager);
      const instance = await EnhancedNetworkManager.deployed();
      console.log("EnhancedNetworkManager deployed at:", instance.address);
    } catch (error) {
      console.error("Error during deployment:", error);
      throw error;
    }
  });
};