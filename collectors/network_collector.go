package collectors

import (
	"fmt"
	"time"

	"windows-agent/models"
	"windows-agent/utils"

	"github.com/sirupsen/logrus"
)

// NetworkCollector collects network-related telemetry data
type NetworkCollector struct {
	agentID string
	logger  *logrus.Logger
	// Track recent connections to avoid duplicates
	recentConnections map[string]time.Time
}

// NetworkConnection represents a simplified network connection
type NetworkConnection struct {
	LocalIP    string
	LocalPort  int
	RemoteIP   string
	RemotePort int
	Protocol   string
	PID        int32
}

// NewNetworkCollector creates a new network collector
func NewNetworkCollector(agentID string, logger *logrus.Logger) *NetworkCollector {
	return &NetworkCollector{
		agentID:           agentID,
		logger:            logger,
		recentConnections: make(map[string]time.Time),
	}
}

// CollectNetworkEvents collects current network connections
func (nc *NetworkCollector) CollectNetworkEvents() ([]models.NetworkEvent, error) {
	var events []models.NetworkEvent
	now := time.Now()

	// For now, create some sample network events
	// In production, you'd use gopsutil to get real connections
	sampleConnections := []NetworkConnection{
		{LocalIP: "127.0.0.1", LocalPort: 8080, RemoteIP: "0.0.0.0", RemotePort: 0, Protocol: "TCP", PID: 1234},
		{LocalIP: "192.168.1.100", LocalPort: 443, RemoteIP: "8.8.8.8", RemotePort: 53, Protocol: "UDP", PID: 5678},
	}

	for _, conn := range sampleConnections {
		// Skip if we've seen this connection recently
		connKey := nc.generateConnectionKey(conn)
		if nc.isRecentlySeen(connKey, now) {
			continue
		}

		// Create network event
		event := nc.createNetworkEvent(conn, now)
		events = append(events, *event)
		nc.recentConnections[connKey] = now
	}

	nc.logger.Infof("Collected %d network events", len(events))
	return events, nil
}

// generateConnectionKey creates a unique key for a connection
func (nc *NetworkCollector) generateConnectionKey(conn NetworkConnection) string {
	return fmt.Sprintf("%s:%d-%s:%d-%s",
		conn.LocalIP, conn.LocalPort,
		conn.RemoteIP, conn.RemotePort,
		conn.Protocol)
}

// isRecentlySeen checks if a connection was recently processed
func (nc *NetworkCollector) isRecentlySeen(connKey string, currentTime time.Time) bool {
	if lastSeen, exists := nc.recentConnections[connKey]; exists {
		return currentTime.Sub(lastSeen) < 2*time.Minute
	}
	return false
}

// createNetworkEvent creates a NetworkEvent from connection information
func (nc *NetworkCollector) createNetworkEvent(conn NetworkConnection, timestamp time.Time) *models.NetworkEvent {
	event := &models.NetworkEvent{
		ID:           utils.GenerateUUID(),
		AgentID:      nc.agentID,
		LocalIP:      conn.LocalIP,
		LocalPort:    conn.LocalPort,
		RemoteIP:     conn.RemoteIP,
		RemotePort:   conn.RemotePort,
		Protocol:     conn.Protocol,
		EventType:    "monitor",
		Timestamp:    timestamp,
		Severity:     nc.determineNetworkSeverity(conn),
		ConnectionID: fmt.Sprintf("%s-%s-%d", conn.LocalIP, conn.RemoteIP, conn.LocalPort),
		CreatedAt:    timestamp,
	}

	// Try to get process information for the connection
	if conn.PID > 0 {
		event.ProcessID = int(conn.PID)
		if processName, err := nc.getProcessName(conn.PID); err == nil {
			event.ProcessName = processName
		}
	}

	return event
}

// determineNetworkSeverity determines the severity level of a network connection
func (nc *NetworkCollector) determineNetworkSeverity(conn NetworkConnection) string {
	// High severity - suspicious remote IPs
	suspiciousIPs := []string{
		"0.0.0.0", "127.0.0.1", "::1", // Localhost
		"192.168.1.1", "10.0.0.1", // Common router IPs
	}

	for _, suspicious := range suspiciousIPs {
		if conn.RemoteIP == suspicious {
			return "low"
		}
	}

	// Medium severity - non-standard ports
	nonStandardPorts := []int{22, 23, 3389, 5900, 8080, 8443, 9000}
	for _, port := range nonStandardPorts {
		if conn.RemotePort == port {
			return "medium"
		}
	}

	// High severity - very high port numbers (potential malware)
	if conn.RemotePort > 49152 {
		return "medium"
	}

	return "low"
}

// getProcessName gets the process name for a given PID
func (nc *NetworkCollector) getProcessName(pid int32) (string, error) {
	// This is a simplified version - in production you'd use gopsutil
	return fmt.Sprintf("process_%d", pid), nil
}

// GetConnectionCount returns the number of active connections
func (nc *NetworkCollector) GetConnectionCount() (int, error) {
	// For now, return a sample count
	// In production, you'd get real connection count
	return 5, nil
}

// CleanupOldConnections removes old entries from the recent connections map
func (nc *NetworkCollector) CleanupOldConnections() {
	cutoff := time.Now().Add(-5 * time.Minute)
	for connKey, lastSeen := range nc.recentConnections {
		if lastSeen.Before(cutoff) {
			delete(nc.recentConnections, connKey)
		}
	}
}

// DetectSuspiciousConnections identifies potentially suspicious network activity
func (nc *NetworkCollector) DetectSuspiciousConnections() ([]models.NetworkEvent, error) {
	var suspiciousEvents []models.NetworkEvent

	// For now, return empty list
	// In production, you'd analyze real connections
	return suspiciousEvents, nil
}
