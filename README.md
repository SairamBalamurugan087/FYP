# Decentralized Network Management Using Blockchain and SDN

## Overview
This project integrates **Blockchain** and **Software Defined Networking (SDN)** to create a **decentralized network management system**. It utilizes **Mininet** for network simulation, **OpenDaylight** as the SDN controller, and **Blockchain** for network management functions like routing, load balancing, and security policy enforcement.

---

## Project Structure
The project structure is organized as follows:

decentralized-network/ 
├── src/ # Source code for the project 
│ ├── contracts/ # Smart contract files for blockchain integration 
│ ├── controller/ # Code for the SDN controller integration with OpenDaylight 
│ ├── network/ # Scripts for network topology and simulation (Mininet) 
│ └── dashboard/ # Web dashboard for monitoring and control 
│ └── templates/ # Template files for the dashboard UI 
├── scripts/ # Utility scripts for the setup and automation 
├── tests/ # Unit tests for validating the functionality of components 
└── config/ # Configuration files for the project setup (e.g., .env)

### Folder Descriptions:

- **`src/`**: Contains the main source code of the project:
  - **`contracts/`**: This folder holds the smart contract files used for blockchain integration and management of the decentralized network.
  - **`controller/`**: Contains code to interact with the SDN controller (OpenDaylight) for managing network topology and flow.
  - **`network/`**: Contains scripts to define and simulate the network topology using **Mininet**, as well as managing network tasks like routing and load balancing.
  - **`dashboard/`**: Contains the web application code for the graphical dashboard used to visualize the network topology and metrics.
    - **`templates/`**: Holds the HTML templates used by the dashboard UI.

- **`scripts/`**: Utility scripts used to simplify tasks like setup, deployments, or management.

- **`tests/`**: Contains unit tests for verifying the correctness and functionality of the project.

- **`config/`**: Configuration files for the system, such as the **`.env`** file that contains environment variables like OpenDaylight credentials and Web3 provider URL.
