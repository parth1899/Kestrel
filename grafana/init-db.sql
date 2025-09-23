# Database Initialization Script
# This script creates sample data for testing Grafana dashboards

# Note: This is a sample script. Replace with your actual database connection details
# and ensure your Windows agent is running to populate real data.

# Tables already created by your application:
# - file_events
# - network_events  
# - process_events
# - system_info
# - telemetry_events
# - threat_indicators

# Add any additional indexes for better Grafana performance
CREATE INDEX IF NOT EXISTS idx_file_events_agent_id ON file_events(agent_id);
CREATE INDEX IF NOT EXISTS idx_file_events_timestamp ON file_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_file_events_event_type ON file_events(event_type);
CREATE INDEX IF NOT EXISTS idx_file_events_severity ON file_events(severity);

CREATE INDEX IF NOT EXISTS idx_network_events_agent_id ON network_events(agent_id);
CREATE INDEX IF NOT EXISTS idx_network_events_timestamp ON network_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_network_events_protocol ON network_events(protocol);
CREATE INDEX IF NOT EXISTS idx_network_events_severity ON network_events(severity);

CREATE INDEX IF NOT EXISTS idx_system_info_agent_id ON system_info(agent_id);
CREATE INDEX IF NOT EXISTS idx_system_info_timestamp ON system_info(timestamp);

CREATE INDEX IF NOT EXISTS idx_threat_indicators_agent_id ON threat_indicators(agent_id);
CREATE INDEX IF NOT EXISTS idx_threat_indicators_timestamp ON threat_indicators(timestamp);
CREATE INDEX IF NOT EXISTS idx_threat_indicators_severity ON threat_indicators(severity);
CREATE INDEX IF NOT EXISTS idx_threat_indicators_status ON threat_indicators(status);