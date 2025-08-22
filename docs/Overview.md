### **Architectural Overview**

* **Agents (Clients):** Lightweight software installed on endpoint devices (desktops, laptops, servers).
* **Cloud Platform (Server):** A centralized, cloud-hosted platform that receives, processes, and stores data from the agents.

The general workflow is as follows:

1.  The agent is installed on an endpoint device.
2.  Upon device startup, the agent establishes a secure connection to the cloud platform.
3.  The agent continuously monitors the endpoint for security-related events.
4.  It sends relevant data (telemetry) to the cloud platform for analysis.
5.  The cloud platform analyzes the data, identifies potential threats, and provides a centralized console for security analysts to manage and respond to incidents.

---
### **The Lightweight Agent**

The agent is a critical component and should be designed with the following characteristics in mind:

* **Low Resource Consumption:** It should have a minimal impact on the performance of the endpoint device.
* **Cross-Platform Compatibility:** The agent should be able to run on various operating systems (Windows, macOS, Linux).
* **Resilience:** It should be difficult for a user or malware to tamper with or disable the agent.
* **Offline Capability:** The agent should be able to continue monitoring and collecting data even when the endpoint is not connected to the internet, and then transmit the data once a connection is re-established.

**Core Functionalities of the Agent:**

* **Data Collection:** The agent collects a wide range of data from the endpoint, such as:
    * Process execution
    * Network connections
    * File system activity
    * Registry changes (on Windows)
    * User login activity
* **Local Analysis:** To reduce the amount of data sent to the cloud and to enable faster detection of some threats, the agent can perform some initial analysis locally.
* **Communication:** The agent is responsible for securely communicating with the cloud platform.

---
### **Cloud Platform**

The cloud platform is the brain of the operation. It needs to be scalable, reliable, and secure. Here are the key components:

* **API Gateway:** This is the single entry point for all incoming traffic from the agents. It handles request routing, composition, and protocol translation. Using an API Gateway helps to decouple the agents from the backend services.
* **Authentication and Authorization:** Every agent needs to be uniquely identified and authenticated before it can send data to the platform. This is often done using certificates or API keys. Authorization ensures that agents only have access to the resources they are permitted to.
* **Data Ingestion and Processing Pipeline:** This is a series of services that process the incoming data from the agents. A typical pipeline might look like this:
    1.  **Data Ingestion:** A highly scalable service that can handle a massive volume of incoming data from the agents.
    2.  **Data Parsing and Enrichment:** The raw data is parsed into a structured format and enriched with additional context (e.g., threat intelligence feeds).
    3.  **Real-time Analysis:** The data is analyzed in real-time to detect suspicious patterns and potential threats. This is often where machine learning models are applied.
    4.  **Alerting:** If a threat is detected, an alert is generated.
* **Database:** A scalable and reliable database is needed to store the vast amount of data collected from the endpoints. Both NoSQL and SQL databases can be used, depending on the specific data and query requirements.
* **Management Console (UI):** A web-based user interface that allows security analysts to:
    * View and investigate alerts.
    * Query the collected data.
    * Manage endpoint policies.
    * Respond to incidents (e.g., by isolating a compromised machine).

---
### **Communication Protocol**

All communication between the agents and the cloud platform must be secure and efficient.

* **HTTPS/TLS:** This is the standard for secure communication over the web. It provides both encryption and authentication.
* **Message Queues:** For reliable data ingestion, message queues (like RabbitMQ or Kafka) are often used. The agent sends data to a message queue, and the data processing pipeline consumes the data from the queue. This decouples the agent from the processing services and provides resilience against failures.

---
### **Key Technologies to Consider**

Here are some technologies you might consider for building such a system:

* **Cloud Provider:**
    * Amazon Web Services (AWS)
    * Microsoft Azure
    * Google Cloud Platform (GCP)
* **API Gateway:**
    * Amazon API Gateway
    * Azure API Management
    * Google Cloud Endpoints
* **Data Ingestion and Processing:**
    * Apache Kafka
    * AWS Kinesis
    * Azure Event Hubs
    * Google Cloud Pub/Sub
* **Database:**
    * Elasticsearch (for search and analytics)
    * Cassandra (NoSQL)
    * PostgreSQL (SQL)
* **Agent Development:**
    * C++ or Rust for high-performance, low-level agents.
    * Go or Python for higher-level logic.

As the name suggests, this major project (BTech) was inspired from Falcon. 
For a high-level overview of the benefits of a platform like this, you might find this video helpful:


[![CrowdStrike Platform Overview](https://img.youtube.com/vi/yxQR9Ih7x_E/maxresdefault.jpg)](https://youtu.be/yxQR9Ih7x_E)
