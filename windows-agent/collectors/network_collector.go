package collectors

import (
	"context"
	"fmt"
	"time"

	"windows-agent/models"
	"windows-agent/utils"

	"github.com/shirou/gopsutil/v3/net"
	"github.com/shirou/gopsutil/v3/process"
	"github.com/sirupsen/logrus"
)

// NetworkCollector collects network-related telemetry data
type NetworkCollector struct {
	agentID           string
	logger            *logrus.Logger
	networkChan       chan models.NetworkEvent // Channel for real-time events
	recentConnections map[string]time.Time
	previousConns     map[string]NetworkConnection // Previous state for diffing
}

// NetworkConnection represents a network connection
type NetworkConnection struct {
	LocalIP    string
	LocalPort  int
	RemoteIP   string
	RemotePort int
	Protocol   string
	PID        int32
	BytesSent  uint64
	BytesRecv  uint64
}

// NewNetworkCollector creates a new network collector
func NewNetworkCollector(agentID string, logger *logrus.Logger) *NetworkCollector {
	return &NetworkCollector{
		agentID:           agentID,
		logger:            logger,
		networkChan:       make(chan models.NetworkEvent, 1000),
		recentConnections: make(map[string]time.Time),
		previousConns:     make(map[string]NetworkConnection),
	}
}

// StartRealTimeMonitoring starts real-time network monitoring
func (nc *NetworkCollector) StartRealTimeMonitoring(ctx context.Context) {
	nc.logger.Info("Starting real-time network monitoring")

	ticker := time.NewTicker(2 * time.Second) // Poll every 2 seconds
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			nc.logger.Info("Stopping network monitoring")
			return

		case <-ticker.C:
			if err := nc.pollNetworkConnections(); err != nil {
				nc.logger.Errorf("Network poll failed: %v", err)
			}
		}
	}
}

// pollNetworkConnections checks for new network connections
func (nc *NetworkCollector) pollNetworkConnections() error {
	// Sample connections multiple times quickly to capture transient connections
	mergedConns := make(map[string]NetworkConnection)
	samples := 3
	sampleDelay := 200 * time.Millisecond

	for i := 0; i < samples; i++ {
		currentConns, err := nc.getCurrentConnections()
		if err != nil {
			// if one sample fails, continue with others
			nc.logger.Debugf("connection sample %d failed: %v", i, err)
		} else {
			for k, v := range currentConns {
				mergedConns[k] = v
			}
		}
		if i < samples-1 {
			time.Sleep(sampleDelay)
		}
	}

	// Find new connections that weren't in previous state
	for key, conn := range mergedConns {
		if _, exists := nc.previousConns[key]; !exists {
			// This is a new connection
			nc.handleNewConnection(conn)
		}
	}

	// Update previous state
	nc.previousConns = mergedConns
	return nil
}

// getCurrentConnections returns current network connections
func (nc *NetworkCollector) getCurrentConnections() (map[string]NetworkConnection, error) {
	conns, err := net.Connections("all")
	if err != nil {
		return nil, fmt.Errorf("failed to get network connections: %v", err)
	}

	currentConns := make(map[string]NetworkConnection)
	for _, conn := range conns {
		if conn.Pid == 0 || conn.Status == "CLOSE" || conn.Status == "NONE" {
			continue
		}

		ncConn := NetworkConnection{
			LocalIP:    conn.Laddr.IP,
			LocalPort:  int(conn.Laddr.Port),
			RemoteIP:   conn.Raddr.IP,
			RemotePort: int(conn.Raddr.Port),
			Protocol:   connTypeToString(conn.Type),
			PID:        conn.Pid,
		}

		key := nc.generateConnectionKey(ncConn)
		currentConns[key] = ncConn
	}

	return currentConns, nil
}

// handleNewConnection processes a new network connection
func (nc *NetworkCollector) handleNewConnection(conn NetworkConnection) {
	// Skip if recently seen
	connKey := nc.generateConnectionKey(conn)
	// Create network event
	event := nc.createNetworkEvent(conn, time.Now())
	nc.recentConnections[connKey] = time.Now()

	// Debug: log the generated IDs and connection key
	if event != nil {
		cid := "<nil>"
		if event.ConnectionID != nil {
			cid = *event.ConnectionID
		}
		nc.logger.Debugf("New connection detected - connKey=%s eventID=%s connectionID=%s pid=%v",
			connKey, event.ID, cid, event.ProcessID)
	} else {
		nc.logger.Debug("New connection detected but event is nil")
	}

	// Send to channel
	select {
	case nc.networkChan <- *event:
		nc.logger.Debugf("Sent network event: %s:%d -> %s:%d (%s) eventID=%s",
			conn.LocalIP, conn.LocalPort, conn.RemoteIP, conn.RemotePort, conn.Protocol, event.ID)
	default:
		nc.logger.Warn("Network event channel full, dropping event")
	}
}

// GetNetworkChannel returns the channel for receiving network events
func (nc *NetworkCollector) GetNetworkChannel() <-chan models.NetworkEvent {
	return nc.networkChan
}

// CollectNetworkEvents collects current network connections using gopsutil
func (nc *NetworkCollector) CollectNetworkEvents() ([]models.NetworkEvent, error) {
	var events []models.NetworkEvent
	now := time.Now()

	// Fetch all TCP and UDP connections
	conns, err := net.Connections("all")
	if err != nil {
		nc.logger.Errorf("Failed to collect network connections: %v", err)
		return nil, fmt.Errorf("failed to get network connections: %v", err)
	}

	for _, conn := range conns {
		// Skip connections without a valid PID or in closed state
		if conn.Pid == 0 || conn.Status == "CLOSE" || conn.Status == "NONE" {
			continue
		}

		// Create a connection struct
		ncConn := NetworkConnection{
			LocalIP:    conn.Laddr.IP,
			LocalPort:  int(conn.Laddr.Port),
			RemoteIP:   conn.Raddr.IP,
			RemotePort: int(conn.Raddr.Port),
			Protocol:   connTypeToString(conn.Type), // Convert uint32 to string
			PID:        conn.Pid,
		}

		// Get byte counters (if available)
		if counters, err := nc.getConnectionCounters(conn); err == nil {
			ncConn.BytesSent = counters.BytesSent
			ncConn.BytesRecv = counters.BytesRecv
		}

		// Create and store network event (do not dedupe by recentConnections so
		// repeated short-lived connections are captured during testing)
		connKey := nc.generateConnectionKey(ncConn)
		event := nc.createNetworkEvent(ncConn, now)
		events = append(events, *event)
		nc.recentConnections[connKey] = now
	}

	// Clean up old connections
	nc.CleanupOldConnections()

	nc.logger.Infof("Collected %d network events", len(events))
	return events, nil
}

// connTypeToString converts connection type uint32 to string
func connTypeToString(connType uint32) string {
	switch connType {
	case 1: // SOCK_STREAM (TCP)
		return "TCP"
	case 2: // SOCK_DGRAM (UDP)
		return "UDP"
	default:
		return "UNKNOWN"
	}
}

// generateConnectionKey creates a unique key for a connection
func (nc *NetworkCollector) generateConnectionKey(conn NetworkConnection) string {
	return fmt.Sprintf("%s:%d-%s:%d-%s-%d",
		conn.LocalIP, conn.LocalPort,
		conn.RemoteIP, conn.RemotePort,
		conn.Protocol, conn.PID)
}

// isRecentlySeen checks if a connection was recently processed
func (nc *NetworkCollector) isRecentlySeen(connKey string, currentTime time.Time) bool {
	// Dedupe disabled for testing/short-lived connection capture. Keep the
	// helper for backward compatibility but always return false so the
	// collector records repeated connections.
	return false
}

// createNetworkEvent creates a NetworkEvent from connection information
func (nc *NetworkCollector) createNetworkEvent(conn NetworkConnection, timestamp time.Time) *models.NetworkEvent {
	// prepare pointer values for nullable fields
	var remoteIP *string
	var remotePort *int
	var bytesSent *int64
	var bytesReceived *int64
	connID := fmt.Sprintf("%s:%d-%s:%d-%s", conn.LocalIP, conn.LocalPort, conn.RemoteIP, conn.RemotePort, conn.Protocol)
	cid := connID

	if conn.RemoteIP != "" {
		remoteIP = &conn.RemoteIP
	}
	if conn.RemotePort != 0 {
		rp := conn.RemotePort
		remotePort = &rp
	}
	if conn.BytesSent != 0 {
		bs := int64(conn.BytesSent)
		bytesSent = &bs
	}
	if conn.BytesRecv != 0 {
		br := int64(conn.BytesRecv)
		bytesReceived = &br
	}

	event := &models.NetworkEvent{
		ID:            utils.GenerateUUID(),
		AgentID:       nc.agentID,
		LocalIP:       conn.LocalIP,
		LocalPort:     conn.LocalPort,
		RemoteIP:      remoteIP,
		RemotePort:    remotePort,
		Protocol:      conn.Protocol,
		EventType:     "connect", // Default to connect for active connections
		Timestamp:     timestamp,
		Severity:      nc.determineNetworkSeverity(conn),
		BytesSent:     bytesSent,
		BytesReceived: bytesReceived,
		ConnectionID:  &cid,
		CreatedAt:     timestamp,
	}

	// Get process information for the connection
	if conn.PID > 0 {
		pid := int(conn.PID)
		event.ProcessID = &pid
		if processName, err := nc.getProcessName(conn.PID); err == nil {
			event.ProcessName = &processName
		}
	}

	return event
}

// determineNetworkSeverity determines the severity level of a network connection
func (nc *NetworkCollector) determineNetworkSeverity(conn NetworkConnection) string {
	// High severity - suspicious remote IPs (expand with threat intel later)
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

	// Medium severity - high port numbers (potential malware)
	if conn.RemotePort > 49152 {
		return "medium"
	}

	// Medium severity - high data transfer (potential exfiltration)
	if conn.BytesSent > 10*1024*1024 || conn.BytesRecv > 10*1024*1024 { // 10MB threshold
		return "medium"
	}

	return "low"
}

// getProcessName gets the process name for a given PID
func (nc *NetworkCollector) getProcessName(pid int32) (string, error) {
	proc, err := process.NewProcess(pid)
	if err != nil {
		return "", fmt.Errorf("failed to get process %d: %v", pid, err)
	}
	name, err := proc.Name()
	if err != nil {
		return "", fmt.Errorf("failed to get process name for PID %d: %v", pid, err)
	}
	return name, nil
}

// getConnectionCounters retrieves sent/received byte counts for a connection
func (nc *NetworkCollector) getConnectionCounters(conn net.ConnectionStat) (net.IOCountersStat, error) {
	// Note: gopsutil/net doesn't provide per-connection bytes directly
	// Approximate by mapping to interface counters (improve with per-socket stats if available)
	counters, err := net.IOCounters(false)
	if err != nil {
		return net.IOCountersStat{}, err
	}
	if len(counters) > 0 {
		return counters[0], nil // Use first interface as a proxy
	}
	return net.IOCountersStat{}, fmt.Errorf("no interface counters available")
}

// GetConnectionCount returns the number of active connections
func (nc *NetworkCollector) GetConnectionCount() (int, error) {
	conns, err := net.Connections("all")
	if err != nil {
		return 0, fmt.Errorf("failed to get connection count: %v", err)
	}
	count := 0
	for _, conn := range conns {
		if conn.Pid != 0 && conn.Status != "CLOSE" && conn.Status != "NONE" {
			count++
		}
	}
	return count, nil
}

// CleanupOldConnections removes old entries from the recent connections map
func (nc *NetworkCollector) CleanupOldConnections() {
	// Shorter retention for recentConnections map to avoid unbounded growth
	// while still allowing short-term dedupe behavior in production scenarios.
	cutoff := time.Now().Add(-30 * time.Second)
	for connKey, lastSeen := range nc.recentConnections {
		if lastSeen.Before(cutoff) {
			delete(nc.recentConnections, connKey)
		}
	}
}

// DetectSuspiciousConnections identifies potentially suspicious network activity
// func (nc *NetworkCollector) DetectSuspiciousConnections() ([]models.NetworkEvent, error) {
// 	var suspiciousEvents []models.NetworkEvent
// 	conns, err := net.Connections("all")
// 	if err != nil {
// 		return nil, fmt.Errorf("failed to get connections for analysis: %v", err)
// 	}

// 	now := time.Now()
// 	for _, conn := range conns {
// 		if conn.Pid == 0 || conn.Status == "CLOSE" || conn.Status != "ESTABLISHED" {
// 			continue
// 		}

// 		ncConn := NetworkConnection{
// 			LocalIP:    conn.Laddr.IP,
// 			LocalPort:  int(conn.Laddr.Port),
// 			RemoteIP:   conn.Raddr.IP,
// 			RemotePort: int(conn.Raddr.Port),
// 			Protocol:   connTypeToString(conn.Type),
// 			PID:        conn.Pid,
// 		}

// 		// Check if connection is suspicious (e.g., high ports or high data)
// 		severity := nc.determineNetworkSeverity(ncConn)
// 		if severity == "medium" || severity == "high" {
// 			event := nc.createNetworkEvent(ncConn, now)
// 			suspiciousEvents = append(suspiciousEvents, *event)
// 		}
// 	}

// 	nc.logger.Infof("Detected %d suspicious network events", len(suspiciousEvents))
// 	return suspiciousEvents, nil
// }
