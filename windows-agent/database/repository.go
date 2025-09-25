package database

import (
	"database/sql"
	"fmt"
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
		       event_type, timestamp, severity, hash, signature, is_scanned, created_at
	       ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
       `

	// prepare nullable values
	var parentProcessID interface{}
	if event.ParentProcessID != nil {
		parentProcessID = *event.ParentProcessID
	} else {
		parentProcessID = nil
	}

	var startTime interface{}
	if event.StartTime != nil {
		startTime = *event.StartTime
	} else {
		startTime = nil
	}

	var endTime interface{}
	if event.EndTime != nil {
		endTime = *event.EndTime
	} else {
		endTime = nil
	}

	var hash interface{}
	if event.Hash != nil {
		hash = *event.Hash
	} else {
		hash = nil
	}

	var signature interface{}
	if event.Signature != nil {
		signature = *event.Signature
	} else {
		signature = nil
	}

	_, err := r.db.DB.Exec(query,
		event.ID, event.AgentID, event.ProcessID, parentProcessID, event.ProcessName,
		event.CommandLine, event.ExecutablePath, event.Username, startTime, endTime,
		event.CPUUsage, event.MemoryUsage, event.EventType, event.Timestamp, event.Severity,
		hash, signature, event.IsScanned, event.CreatedAt)
	return err
}

func (r *Repository) GetProcessEvents(agentID string, limit int) ([]models.ProcessEvent, error) {
	query := `
	       SELECT id, agent_id, process_id, parent_process_id, process_name, command_line,
		       executable_path, username, start_time, end_time, cpu_usage, memory_usage,
		       event_type, timestamp, severity, hash, signature, is_scanned, created_at
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
		var parentPID sql.NullInt64
		var startTime sql.NullTime
		var endTime sql.NullTime
		var cpuUsage sql.NullFloat64
		var memoryUsage sql.NullInt64
		var hash sql.NullString
		var signature sql.NullString

		err := rows.Scan(&event.ID, &event.AgentID, &event.ProcessID, &parentPID,
			&event.ProcessName, &event.CommandLine, &event.ExecutablePath, &event.Username,
			&startTime, &endTime, &cpuUsage, &memoryUsage,
			&event.EventType, &event.Timestamp, &event.Severity, &hash, &signature,
			&event.IsScanned, &event.CreatedAt)
		if err != nil {
			return nil, err
		}

		if parentPID.Valid {
			v := int(parentPID.Int64)
			event.ParentProcessID = &v
		} else {
			event.ParentProcessID = nil
		}

		if startTime.Valid {
			t := startTime.Time
			event.StartTime = &t
		} else {
			event.StartTime = nil
		}

		if endTime.Valid {
			t := endTime.Time
			event.EndTime = &t
		} else {
			event.EndTime = nil
		}

		if cpuUsage.Valid {
			event.CPUUsage = cpuUsage.Float64
		} else {
			event.CPUUsage = 0
		}

		if memoryUsage.Valid {
			event.MemoryUsage = memoryUsage.Int64
		} else {
			event.MemoryUsage = 0
		}

		if hash.Valid {
			h := hash.String
			event.Hash = &h
		} else {
			event.Hash = nil
		}

		if signature.Valid {
			s := signature.String
			event.Signature = &s
		} else {
			event.Signature = nil
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
		       timestamp, severity, file_size, file_hash, file_type, is_scanned, created_at
	       ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
       `

	var processID interface{}
	if event.ProcessID != nil {
		processID = *event.ProcessID
	} else {
		processID = nil
	}

	var processName interface{}
	if event.ProcessName != nil {
		processName = *event.ProcessName
	} else {
		processName = nil
	}

	var fileSize interface{}
	if event.FileSize != nil {
		fileSize = *event.FileSize
	} else {
		fileSize = nil
	}

	var fileHash interface{}
	if event.FileHash != nil {
		fileHash = *event.FileHash
	} else {
		fileHash = nil
	}

	var fileType interface{}
	if event.FileType != nil {
		fileType = *event.FileType
	} else {
		fileType = nil
	}

	_, err := r.db.DB.Exec(query,
		event.ID, event.AgentID, processID, processName, event.FilePath,
		event.FileName, event.EventType, event.Timestamp, event.Severity, fileSize,
		fileHash, fileType, event.IsScanned, event.CreatedAt)
	return err
}

func (r *Repository) GetFileEvents(agentID string, limit int) ([]models.FileEvent, error) {
	query := `
	       SELECT id, agent_id, process_id, process_name, file_path, file_name, event_type,
		       timestamp, severity, file_size, file_hash, file_type, is_scanned, created_at
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
		var processID sql.NullInt64
		var processName sql.NullString
		var fileSize sql.NullInt64
		var fileHash sql.NullString
		var fileType sql.NullString

		err := rows.Scan(&event.ID, &event.AgentID, &processID, &processName,
			&event.FilePath, &event.FileName, &event.EventType, &event.Timestamp,
			&event.Severity, &fileSize, &fileHash, &fileType, &event.IsScanned, &event.CreatedAt)
		if err != nil {
			return nil, err
		}

		if processID.Valid {
			v := int(processID.Int64)
			event.ProcessID = &v
		} else {
			event.ProcessID = nil
		}

		if processName.Valid {
			s := processName.String
			event.ProcessName = &s
		} else {
			event.ProcessName = nil
		}

		if fileSize.Valid {
			v := fileSize.Int64
			event.FileSize = &v
		} else {
			event.FileSize = nil
		}

		if fileHash.Valid {
			s := fileHash.String
			event.FileHash = &s
		} else {
			event.FileHash = nil
		}

		if fileType.Valid {
			s := fileType.String
			event.FileType = &s
		} else {
			event.FileType = nil
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
		       bytes_received, connection_id, is_scanned, created_at
	       ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
       `

	var processID interface{}
	if event.ProcessID != nil {
		processID = *event.ProcessID
	} else {
		processID = nil
	}

	var processName interface{}
	if event.ProcessName != nil {
		processName = *event.ProcessName
	} else {
		processName = nil
	}

	var remoteIP interface{}
	if event.RemoteIP != nil {
		remoteIP = *event.RemoteIP
	} else {
		remoteIP = nil
	}

	var remotePort interface{}
	if event.RemotePort != nil {
		remotePort = *event.RemotePort
	} else {
		remotePort = nil
	}

	var bytesSent interface{}
	if event.BytesSent != nil {
		bytesSent = *event.BytesSent
	} else {
		bytesSent = nil
	}

	var bytesReceived interface{}
	if event.BytesReceived != nil {
		bytesReceived = *event.BytesReceived
	} else {
		bytesReceived = nil
	}

	var connectionID interface{}
	if event.ConnectionID != nil {
		connectionID = *event.ConnectionID
	} else {
		connectionID = nil
	}

	res, err := r.db.DB.Exec(query,
		event.ID, event.AgentID, processID, processName, event.LocalIP,
		event.LocalPort, remoteIP, remotePort, event.Protocol, event.EventType,
		event.Timestamp, event.Severity, bytesSent, bytesReceived, connectionID,
		event.IsScanned, event.CreatedAt)

	// Debug log the result for troubleshooting duplicate/insert issues
	if err != nil {
		// Use Printf-style to avoid importing logger here; repository is low-level
		// but printing to stdout/stderr may be visible in the agent logs.
		// Prefer to return the error after logging.
		fmtErr := fmt.Errorf("SaveNetworkEvent Exec failed: %w", err)
		return fmtErr
	}

	// Try to get affected rows if driver supports it
	if res != nil {
		// we won't rely on RowsAffected for logic, but log it when possible
		if rowsAffected, err2 := res.RowsAffected(); err2 == nil {
			_ = rowsAffected // noop for now; caller can add logging if needed
		}
	}

	return nil
}

func (r *Repository) GetNetworkEvents(agentID string, limit int) ([]models.NetworkEvent, error) {
	query := `
	       SELECT id, agent_id, process_id, process_name, local_ip, local_port, remote_ip,
		       remote_port, protocol, event_type, timestamp, severity, bytes_sent,
		       bytes_received, connection_id, is_scanned, created_at
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
		var processID sql.NullInt64
		var processName sql.NullString
		var remoteIP sql.NullString
		var remotePort sql.NullInt64
		var bytesSent sql.NullInt64
		var bytesReceived sql.NullInt64
		var connectionID sql.NullString

		err := rows.Scan(&event.ID, &event.AgentID, &processID, &processName,
			&event.LocalIP, &event.LocalPort, &remoteIP, &remotePort,
			&event.Protocol, &event.EventType, &event.Timestamp, &event.Severity,
			&bytesSent, &bytesReceived, &connectionID, &event.IsScanned, &event.CreatedAt)
		if err != nil {
			return nil, err
		}

		if processID.Valid {
			v := int(processID.Int64)
			event.ProcessID = &v
		} else {
			event.ProcessID = nil
		}

		if processName.Valid {
			s := processName.String
			event.ProcessName = &s
		} else {
			event.ProcessName = nil
		}

		if remoteIP.Valid {
			s := remoteIP.String
			event.RemoteIP = &s
		} else {
			event.RemoteIP = nil
		}

		if remotePort.Valid {
			v := int(remotePort.Int64)
			event.RemotePort = &v
		} else {
			event.RemotePort = nil
		}

		if bytesSent.Valid {
			v := bytesSent.Int64
			event.BytesSent = &v
		} else {
			event.BytesSent = nil
		}

		if bytesReceived.Valid {
			v := bytesReceived.Int64
			event.BytesReceived = &v
		} else {
			event.BytesReceived = nil
		}

		if connectionID.Valid {
			s := connectionID.String
			event.ConnectionID = &s
		} else {
			event.ConnectionID = nil
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
