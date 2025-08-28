package database

import (
	"database/sql"
	"time"

	"windows-agent/models"
)

// Repository provides database operations for telemetry data
type Repository struct {
	db *PostgresDB
}

// NewRepository creates a new repository instance
func NewRepository(db *PostgresDB) *Repository {
	return &Repository{db: db}
}

// TelemetryEventRepository methods
func (r *Repository) SaveTelemetryEvent(event *models.TelemetryEvent) error {
	query := `
		INSERT INTO telemetry_events (id, agent_id, event_type, timestamp, severity, data, processed, created_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
	`

	dataJSON, ok := event.Data["json"].(string)
	if !ok {
		dataJSON = "{}"
	}

	_, err := r.db.DB.Exec(query, event.ID, event.AgentID, event.EventType, event.Timestamp,
		event.Severity, dataJSON, event.Processed, event.CreatedAt)
	return err
}

func (r *Repository) GetTelemetryEvents(agentID string, limit int) ([]models.TelemetryEvent, error) {
	query := `
		SELECT id, agent_id, event_type, timestamp, severity, data, processed, created_at
		FROM telemetry_events 
		WHERE agent_id = $1 
		ORDER BY timestamp DESC 
		LIMIT $2
	`

	rows, err := r.db.DB.Query(query, agentID, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var events []models.TelemetryEvent
	for rows.Next() {
		var event models.TelemetryEvent
		var dataJSON string
		err := rows.Scan(&event.ID, &event.AgentID, &event.EventType, &event.Timestamp,
			&event.Severity, &dataJSON, &event.Processed, &event.CreatedAt)
		if err != nil {
			return nil, err
		}
		event.Data = map[string]interface{}{"json": dataJSON}
		events = append(events, event)
	}

	return events, nil
}

// ProcessEventRepository methods
func (r *Repository) SaveProcessEvent(event *models.ProcessEvent) error {
	query := `
		INSERT INTO process_events (
			id, agent_id, process_id, parent_process_id, process_name, command_line, 
			executable_path, username, start_time, end_time, cpu_usage, memory_usage, 
			event_type, timestamp, severity, hash, signature, created_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
	`

	_, err := r.db.DB.Exec(query,
		event.ID, event.AgentID, event.ProcessID, event.ParentProcessID, event.ProcessName,
		event.CommandLine, event.ExecutablePath, event.Username, event.StartTime, event.EndTime,
		event.CPUUsage, event.MemoryUsage, event.EventType, event.Timestamp, event.Severity,
		event.Hash, event.Signature, event.CreatedAt)
	return err
}

func (r *Repository) GetProcessEvents(agentID string, limit int) ([]models.ProcessEvent, error) {
	query := `
		SELECT id, agent_id, process_id, parent_process_id, process_name, command_line,
			executable_path, username, start_time, end_time, cpu_usage, memory_usage,
			event_type, timestamp, severity, hash, signature, created_at
		FROM process_events 
		WHERE agent_id = $1 
		ORDER BY timestamp DESC 
		LIMIT $2
	`

	rows, err := r.db.DB.Query(query, agentID, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var events []models.ProcessEvent
	for rows.Next() {
		var event models.ProcessEvent
		err := rows.Scan(&event.ID, &event.AgentID, &event.ProcessID, &event.ParentProcessID,
			&event.ProcessName, &event.CommandLine, &event.ExecutablePath, &event.Username,
			&event.StartTime, &event.EndTime, &event.CPUUsage, &event.MemoryUsage,
			&event.EventType, &event.Timestamp, &event.Severity, &event.Hash, &event.Signature,
			&event.CreatedAt)
		if err != nil {
			return nil, err
		}
		events = append(events, event)
	}

	return events, nil
}

// FileEventRepository methods
func (r *Repository) SaveFileEvent(event *models.FileEvent) error {
	query := `
		INSERT INTO file_events (
			id, agent_id, process_id, process_name, file_path, file_name, event_type,
			timestamp, severity, file_size, file_hash, file_type, created_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
	`

	_, err := r.db.DB.Exec(query,
		event.ID, event.AgentID, event.ProcessID, event.ProcessName, event.FilePath,
		event.FileName, event.EventType, event.Timestamp, event.Severity, event.FileSize,
		event.FileHash, event.FileType, event.CreatedAt)
	return err
}

func (r *Repository) GetFileEvents(agentID string, limit int) ([]models.FileEvent, error) {
	query := `
		SELECT id, agent_id, process_id, process_name, file_path, file_name, event_type,
			timestamp, severity, file_size, file_hash, file_type, created_at
		FROM file_events 
		WHERE agent_id = $1 
		ORDER BY timestamp DESC 
		LIMIT $2
	`

	rows, err := r.db.DB.Query(query, agentID, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var events []models.FileEvent
	for rows.Next() {
		var event models.FileEvent
		err := rows.Scan(&event.ID, &event.AgentID, &event.ProcessID, &event.ProcessName,
			&event.FilePath, &event.FileName, &event.EventType, &event.Timestamp,
			&event.Severity, &event.FileSize, &event.FileHash, &event.FileType, &event.CreatedAt)
		if err != nil {
			return nil, err
		}
		events = append(events, event)
	}

	return events, nil
}

// NetworkEventRepository methods
func (r *Repository) SaveNetworkEvent(event *models.NetworkEvent) error {
	query := `
		INSERT INTO network_events (
			id, agent_id, process_id, process_name, local_ip, local_port, remote_ip,
			remote_port, protocol, event_type, timestamp, severity, bytes_sent,
			bytes_received, connection_id, created_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
	`

	_, err := r.db.DB.Exec(query,
		event.ID, event.AgentID, event.ProcessID, event.ProcessName, event.LocalIP,
		event.LocalPort, event.RemoteIP, event.RemotePort, event.Protocol, event.EventType,
		event.Timestamp, event.Severity, event.BytesSent, event.BytesReceived, event.ConnectionID,
		event.CreatedAt)
	return err
}

func (r *Repository) GetNetworkEvents(agentID string, limit int) ([]models.NetworkEvent, error) {
	query := `
		SELECT id, agent_id, process_id, process_name, local_ip, local_port, remote_ip,
			remote_port, protocol, event_type, timestamp, severity, bytes_sent,
			bytes_received, connection_id, created_at
		FROM network_events 
		WHERE agent_id = $1 
		ORDER BY timestamp DESC 
		LIMIT $2
	`

	rows, err := r.db.DB.Query(query, agentID, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var events []models.NetworkEvent
	for rows.Next() {
		var event models.NetworkEvent
		err := rows.Scan(&event.ID, &event.AgentID, &event.ProcessID, &event.ProcessName,
			&event.LocalIP, &event.LocalPort, &event.RemoteIP, &event.RemotePort,
			&event.Protocol, &event.EventType, &event.Timestamp, &event.Severity,
			&event.BytesSent, &event.BytesReceived, &event.ConnectionID, &event.CreatedAt)
		if err != nil {
			return nil, err
		}
		events = append(events, event)
	}

	return events, nil
}

// SystemInfoRepository methods
func (r *Repository) SaveSystemInfo(info *models.SystemInfo) error {
	query := `
		INSERT INTO system_info (
			id, agent_id, hostname, os_version, architecture, total_memory,
			available_memory, cpu_count, cpu_usage, disk_usage, uptime, timestamp, created_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
	`

	_, err := r.db.DB.Exec(query,
		info.ID, info.AgentID, info.Hostname, info.OSVersion, info.Architecture,
		info.TotalMemory, info.AvailableMemory, info.CPUCount, info.CPUUsage,
		info.DiskUsage, info.Uptime, info.Timestamp, info.CreatedAt)
	return err
}

func (r *Repository) GetLatestSystemInfo(agentID string) (*models.SystemInfo, error) {
	query := `
		SELECT id, agent_id, hostname, os_version, architecture, total_memory,
			available_memory, cpu_count, cpu_usage, disk_usage, uptime, timestamp, created_at
		FROM system_info 
		WHERE agent_id = $1 
		ORDER BY timestamp DESC 
		LIMIT 1
	`

	var info models.SystemInfo
	err := r.db.DB.QueryRow(query, agentID).Scan(
		&info.ID, &info.AgentID, &info.Hostname, &info.OSVersion, &info.Architecture,
		&info.TotalMemory, &info.AvailableMemory, &info.CPUCount, &info.CPUUsage,
		&info.DiskUsage, &info.Uptime, &info.Timestamp, &info.CreatedAt)

	if err == sql.ErrNoRows {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}

	return &info, nil
}

// ThreatIndicatorRepository methods
func (r *Repository) SaveThreatIndicator(indicator *models.ThreatIndicator) error {
	query := `
		INSERT INTO threat_indicators (
			id, agent_id, event_id, event_type, threat_type, description,
			confidence, severity, timestamp, status, created_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
	`

	_, err := r.db.DB.Exec(query,
		indicator.ID, indicator.AgentID, indicator.EventID, indicator.EventType,
		indicator.ThreatType, indicator.Description, indicator.Confidence,
		indicator.Severity, indicator.Timestamp, indicator.Status, indicator.CreatedAt)
	return err
}

func (r *Repository) GetThreatIndicators(agentID string, status string, limit int) ([]models.ThreatIndicator, error) {
	query := `
		SELECT id, agent_id, event_id, event_type, threat_type, description,
			confidence, severity, timestamp, status, created_at
		FROM threat_indicators 
		WHERE agent_id = $1 AND status = $2
		ORDER BY timestamp DESC 
		LIMIT $3
	`

	rows, err := r.db.DB.Query(query, agentID, status, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var indicators []models.ThreatIndicator
	for rows.Next() {
		var indicator models.ThreatIndicator
		err := rows.Scan(&indicator.ID, &indicator.AgentID, &indicator.EventID,
			&indicator.EventType, &indicator.ThreatType, &indicator.Description,
			&indicator.Confidence, &indicator.Severity, &indicator.Timestamp,
			&indicator.Status, &indicator.CreatedAt)
		if err != nil {
			return nil, err
		}
		indicators = append(indicators, indicator)
	}

	return indicators, nil
}

// UpdateThreatIndicatorStatus updates the status of a threat indicator
func (r *Repository) UpdateThreatIndicatorStatus(id, status string) error {
	query := `UPDATE threat_indicators SET status = $1 WHERE id = $2`
	_, err := r.db.DB.Exec(query, status, id)
	return err
}

// GetEventCount returns the count of events for a specific agent and event type
func (r *Repository) GetEventCount(agentID, eventType string, since time.Time) (int, error) {
	var count int
	query := `
		SELECT COUNT(*) FROM telemetry_events 
		WHERE agent_id = $1 AND event_type = $2 AND timestamp >= $3
	`
	err := r.db.DB.QueryRow(query, agentID, eventType, since).Scan(&count)
	return count, err
}
