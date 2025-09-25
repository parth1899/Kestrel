package models

import (
	"time"
)

// TelemetryEvent represents a generic telemetry event
type TelemetryEvent struct {
	ID        string                 `json:"id"`
	AgentID   string                 `json:"agent_id"`
	EventType string                 `json:"event_type"`
	Timestamp time.Time              `json:"timestamp"`
	Severity  string                 `json:"severity"`
	Data      map[string]interface{} `json:"data"`
	Processed bool                   `json:"processed"`
	CreatedAt time.Time              `json:"created_at"`
}

// ProcessEvent represents process-related telemetry data
type ProcessEvent struct {
	ID              string     `json:"id"`
	AgentID         string     `json:"agent_id"`
	ProcessID       int        `json:"process_id"`
	ParentProcessID *int       `json:"parent_process_id,omitempty"`
	ProcessName     string     `json:"process_name"`
	CommandLine     string     `json:"command_line"`
	ExecutablePath  string     `json:"executable_path"`
	Username        string     `json:"username"`
	StartTime       *time.Time `json:"start_time,omitempty"`
	EndTime         *time.Time `json:"end_time,omitempty"`
	CPUUsage        float64    `json:"cpu_usage"`
	MemoryUsage     int64      `json:"memory_usage"`
	EventType       string     `json:"event_type"` // start, stop, modify
	Timestamp       time.Time  `json:"timestamp"`
	Severity        string     `json:"severity"`
	Hash            *string    `json:"hash,omitempty"`
	Signature       *string    `json:"signature,omitempty"`
	IsScanned       bool       `json:"is_scanned"`
	CreatedAt       time.Time  `json:"created_at"`
}

// FileEvent represents file system activity
type FileEvent struct {
	ID          string    `json:"id"`
	AgentID     string    `json:"agent_id"`
	ProcessID   *int      `json:"process_id,omitempty"`
	ProcessName *string   `json:"process_name,omitempty"`
	FilePath    string    `json:"file_path"`
	FileName    string    `json:"file_name"`
	EventType   string    `json:"event_type"` // create, modify, delete, access
	Timestamp   time.Time `json:"timestamp"`
	Severity    string    `json:"severity"`
	FileSize    *int64    `json:"file_size,omitempty"`
	FileHash    *string   `json:"file_hash,omitempty"`
	FileType    *string   `json:"file_type,omitempty"`
	IsScanned   bool      `json:"is_scanned"`
	CreatedAt   time.Time `json:"created_at"`
}

// NetworkEvent represents network activity
type NetworkEvent struct {
	ID            string    `json:"id"`
	AgentID       string    `json:"agent_id"`
	ProcessID     *int      `json:"process_id,omitempty"`
	ProcessName   *string   `json:"process_name,omitempty"`
	LocalIP       string    `json:"local_ip"`
	LocalPort     int       `json:"local_port"`
	RemoteIP      *string   `json:"remote_ip,omitempty"`
	RemotePort    *int      `json:"remote_port,omitempty"`
	Protocol      string    `json:"protocol"`
	EventType     string    `json:"event_type"` // connect, disconnect, send, receive
	Timestamp     time.Time `json:"timestamp"`
	Severity      string    `json:"severity"`
	BytesSent     *int64    `json:"bytes_sent,omitempty"`
	BytesReceived *int64    `json:"bytes_received,omitempty"`
	ConnectionID  *string   `json:"connection_id,omitempty"`
	IsScanned     bool      `json:"is_scanned"`
	CreatedAt     time.Time `json:"created_at"`
}

// SystemInfo represents system information
type SystemInfo struct {
	ID              string    `json:"id"`
	AgentID         string    `json:"agent_id"`
	Hostname        string    `json:"hostname"`
	OSVersion       string    `json:"os_version"`
	Architecture    string    `json:"architecture"`
	TotalMemory     uint64    `json:"total_memory"`
	AvailableMemory uint64    `json:"available_memory"`
	CPUCount        int       `json:"cpu_count"`
	CPUUsage        float64   `json:"cpu_usage"`
	DiskUsage       float64   `json:"disk_usage"`
	Uptime          int64     `json:"uptime"`
	Timestamp       time.Time `json:"timestamp"`
	CreatedAt       time.Time `json:"created_at"`
}

// ThreatIndicator represents potential security threats
type ThreatIndicator struct {
	ID          string    `json:"id"`
	AgentID     string    `json:"agent_id"`
	EventID     string    `json:"event_id"`
	EventType   string    `json:"event_type"`
	ThreatType  string    `json:"threat_type"`
	Description string    `json:"description"`
	Confidence  float64   `json:"confidence"`
	Severity    string    `json:"severity"`
	Timestamp   time.Time `json:"timestamp"`
	Status      string    `json:"status"` // new, investigating, resolved, false_positive
	CreatedAt   time.Time `json:"created_at"`
}
