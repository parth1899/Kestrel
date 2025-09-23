# Grafana Analytics Setup for NXTGEN Threat Detection Platform

This guide will help you set up Grafana dashboards to visualize analytics from your threat detection platform's database.

## Prerequisites

- Docker and Docker Compose installed
- Your Windows agent collecting data to PostgreSQL database
- Database tables: `file_events`, `network_events`, `process_events`, `system_info`, `telemetry_events`, `threat_indicators`

## Quick Start

1. **Start the Services**

   ```powershell
   # Navigate to the project directory
   cd "e:\Final Year\EDAI7\NXTGEN-Threat-Detection-Platform"

   # Start Grafana and PostgreSQL
   docker-compose up -d
   ```

2. **Access Grafana**

   - URL: http://localhost:3000
   - Username: `admin`
   - Password: `admin123`

3. **Database Connection**
   The PostgreSQL datasource is automatically configured with:
   - Host: `postgres:5432`
   - Database: `threat_detection`
   - Username: `threat_user`
   - Password: `threat_password123`

## Available Dashboards

### 1. Threat Detection Overview (`threat-overview`)

**Main security operations center dashboard**

- **Key Metrics Cards:**
  - Total Events (24h)
  - Critical Events (24h)
  - Active Agents
  - Active Threats
- **Visualizations:**
  - Event Timeline by Type (Process, File, Network)
  - Event Severity Distribution
  - Recent Threat Indicators Table
- **Use Cases:**
  - Security team daily briefings
  - Executive security status reports
  - High-level threat monitoring

### 2. Process Activity Dashboard (`process-activity`)

**Detailed process monitoring and analysis**

- **Visualizations:**
  - Process Events Distribution (Pie Chart)
  - Process Events Timeline (5-minute intervals)
  - Recent Process Events Table with severity indicators
- **Key Information:**
  - Process names and command lines
  - User context (username)
  - Event types (start, stop, modify)
  - Severity levels with color coding
- **Use Cases:**
  - Malware process detection
  - Unusual process activity investigation
  - User behavior analysis

### 3. Network Activity Dashboard (`network-activity`)

**Network communications and traffic analysis**

- **Visualizations:**
  - Network Protocol Distribution
  - Network Traffic Over Time (bytes sent/received)
  - Top Remote IPs (last hour)
  - Recent Network Connections Table
- **Key Information:**
  - Protocol breakdown (TCP, UDP, etc.)
  - Connection patterns
  - Data volume analysis
  - Remote endpoint identification
- **Use Cases:**
  - Data exfiltration detection
  - Command & control communication identification
  - Network baseline establishment

### 4. File System Activity Dashboard (`file-activity`)

**File operations and integrity monitoring**

- **Visualizations:**
  - File Event Types Distribution (create, modify, delete, access)
  - File Activity Timeline
  - Top File Types Accessed
  - Recent File Activities Table
- **Key Information:**
  - File operation types
  - File sizes and types
  - Process-to-file relationships
  - File access patterns
- **Use Cases:**
  - Ransomware detection (mass file modifications)
  - Data theft monitoring
  - System integrity validation

### 5. System Performance Dashboard (`system-performance`)

**Endpoint health and performance monitoring**

- **Visualizations:**
  - Current CPU, Memory, Disk Usage (Gauges)
  - System Uptime
  - CPU Usage Over Time
  - Memory Usage Over Time
  - System Information History Table
- **Key Information:**
  - Real-time resource utilization
  - Performance trends
  - System specifications
  - Historical performance data
- **Use Cases:**
  - Performance impact assessment
  - Resource exhaustion detection
  - Capacity planning

## Dashboard Features

### Time Controls

- **Default Range:** Last 6 hours (adjustable)
- **Refresh Rate:** 30 seconds auto-refresh
- **Time Picker:** Flexible time range selection

### Interactive Elements

- **Drill-down Capabilities:** Click on charts to filter data
- **Sortable Tables:** Sort by any column
- **Color-coded Severity:** Visual severity indicators
- **Responsive Design:** Works on desktop and mobile

### Data Refresh

- **Real-time Updates:** 30-second refresh interval
- **Live Data:** Shows current and historical data
- **Performance Optimized:** Efficient queries with proper indexing

## Advanced Configuration

### Custom Queries

You can modify dashboard queries by:

1. Edit mode → Panel → Query tab
2. Modify SQL queries for specific needs
3. Add custom filters or aggregations

### Alerting Setup

Configure alerts for:

- High volume of critical events
- Unusual network traffic patterns
- System performance thresholds
- New threat indicators

### Additional Datasources

To connect to existing databases:

1. Configuration → Data Sources → Add data source
2. Configure PostgreSQL connection
3. Update dashboard queries accordingly

## Troubleshooting

### Common Issues

**Dashboard Not Loading Data:**

- Verify database connection in Data Sources
- Check table names match your schema
- Ensure Windows agent is writing data

**Performance Issues:**

- Add database indexes for timestamp columns
- Limit query time ranges
- Optimize panel refresh intervals

**Permission Errors:**

- Verify PostgreSQL user permissions
- Check network connectivity between containers

### Maintenance

**Regular Tasks:**

- Database cleanup for old data
- Dashboard backup and version control
- Query performance optimization
- Alert threshold tuning

## Security Considerations

- **Access Control:** Configure Grafana user roles and permissions
- **Database Security:** Use strong passwords and network isolation
- **Data Retention:** Implement data lifecycle policies
- **Audit Logging:** Enable Grafana audit logs

## Extension Ideas

### Additional Dashboards

- **Agent Health Monitoring:** Agent connectivity and performance
- **Threat Intelligence:** Integration with threat feeds
- **Compliance Reporting:** Regulatory compliance metrics
- **User Behavior Analytics:** User activity patterns

### Integration Options

- **SIEM Integration:** Forward alerts to security platforms
- **Notification Channels:** Slack, Email, PagerDuty alerts
- **API Integration:** Custom threat intelligence feeds
- **Machine Learning:** Anomaly detection overlays

## Support

For issues or enhancements:

1. Check Grafana documentation: https://grafana.com/docs/
2. Review PostgreSQL query optimization guides
3. Monitor system logs for errors
4. Consider professional Grafana support for enterprise deployments

---

**Note:** Ensure your Windows agent is actively collecting data before expecting to see visualizations. The dashboards are designed to work with the existing database schema defined in your telemetry models.
