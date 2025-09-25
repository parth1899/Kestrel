package main

import (
	"database/sql"
	"fmt"
	"log"
	"time"
)

// Alert represents an alert to be inserted into the alerts table
// You may want to move this to models/ if you want to reuse it

type Alert struct {
	EventID       string
	Indicator     string
	IndicatorType string
	ThreatInfo    string
	Severity      string
	Status        string
	CreatedAt     time.Time
}

// RunThreatScanner runs the threat scanning logic using the provided database connection
func RunThreatScanner(db *sql.DB) {
	// 1. Query for unscanned file events
	fileEvents, err := getUnscannedFileEvents(db)
	if err != nil {
		log.Printf("Failed to get file events: %v", err)
		return
	}
	for _, fe := range fileEvents {
		// default: mark as scanned even if no match so we don't reprocess endlessly
		scanned := false
		if fe.FileHash != nil {
			if match, info := checkFileHash(db, *fe.FileHash); match {
				alert := Alert{
					EventID:       fe.ID,
					Indicator:     *fe.FileHash,
					IndicatorType: "file_hash",
					ThreatInfo:    info,
					Severity:      "High",
					Status:        "New",
					CreatedAt:     time.Now(),
				}
				insertAlert(db, alert)
				scanned = true
			}
		}
		if err := markFileEventScanned(db, fe.ID); err != nil {
			log.Printf("Failed to mark file event scanned (id=%s): %v", fe.ID, err)
		} else if scanned {
			log.Printf("File event scanned and alert created (id=%s)", fe.ID)
		}
	}

	// 2. Query for unscanned network events
	netEvents, err := getUnscannedNetworkEvents(db)
	if err != nil {
		log.Printf("Failed to get network events: %v", err)
		return
	}
	for _, ne := range netEvents {
		scanned := false
		if ne.RemoteIP != nil {
			if match, info := checkIP(db, *ne.RemoteIP); match {
				alert := Alert{
					EventID:       ne.ID,
					Indicator:     *ne.RemoteIP,
					IndicatorType: "ip_address",
					ThreatInfo:    info,
					Severity:      "High",
					Status:        "New",
					CreatedAt:     time.Now(),
				}
				insertAlert(db, alert)
				scanned = true
			}
		}
		if err := markNetworkEventScanned(db, ne.ID); err != nil {
			log.Printf("Failed to mark network event scanned (id=%s): %v", ne.ID, err)
		} else if scanned {
			log.Printf("Network event scanned and alert created (id=%s)", ne.ID)
		}
		// No domain_name field in network_events schema, so skip domain check
	}

	// 3. Query for unscanned process events
	procEvents, err := getUnscannedProcessEvents(db)
	if err != nil {
		log.Printf("Failed to get process events: %v", err)
		return
	}
	for _, pe := range procEvents {
		scanned := false
		if pe.Hash != nil {
			if match, info := checkFileHash(db, *pe.Hash); match {
				alert := Alert{
					EventID:       pe.ID,
					Indicator:     *pe.Hash,
					IndicatorType: "process_hash",
					ThreatInfo:    info,
					Severity:      "High",
					Status:        "New",
					CreatedAt:     time.Now(),
				}
				insertAlert(db, alert)
				scanned = true
			}
		}
		if err := markProcessEventScanned(db, pe.ID); err != nil {
			log.Printf("Failed to mark process event scanned (id=%s): %v", pe.ID, err)
		} else if scanned {
			log.Printf("Process event scanned and alert created (id=%s)", pe.ID)
		}
	}
}

// markFileEventScanned sets is_scanned=true for the given file event id
func markFileEventScanned(db *sql.DB, id string) error {
	_, err := db.Exec(`UPDATE file_events SET is_scanned = true WHERE id = $1`, id)
	return err
}

// markNetworkEventScanned sets is_scanned=true for the given network event id
func markNetworkEventScanned(db *sql.DB, id string) error {
	_, err := db.Exec(`UPDATE network_events SET is_scanned = true WHERE id = $1`, id)
	return err
}

// markProcessEventScanned sets is_scanned=true for the given process event id
func markProcessEventScanned(db *sql.DB, id string) error {
	_, err := db.Exec(`UPDATE process_events SET is_scanned = true WHERE id = $1`, id)
	return err
}

// --- Helper functions and types ---

type FileEvent struct {
	ID          string
	AgentID     string
	ProcessID   *int
	ProcessName *string
	FilePath    string
	FileName    string
	EventType   string
	Timestamp   time.Time
	Severity    string
	FileSize    *int64
	FileHash    *string
	FileType    *string
	IsScanned   bool
	CreatedAt   time.Time
}

type NetworkEvent struct {
	ID            string
	AgentID       string
	ProcessID     *int
	ProcessName   *string
	LocalIP       string
	LocalPort     int
	RemoteIP      *string
	RemotePort    *int
	Protocol      string
	EventType     string
	Timestamp     time.Time
	Severity      string
	BytesSent     *int64
	BytesReceived *int64
	ConnectionID  *string
	IsScanned     bool
	CreatedAt     time.Time
}

type ProcessEvent struct {
	ID              string
	AgentID         string
	ProcessID       int
	ParentProcessID *int
	ProcessName     string
	CommandLine     string
	ExecutablePath  string
	Username        string
	StartTime       *time.Time
	EndTime         *time.Time
	CPUUsage        float64
	MemoryUsage     int64
	EventType       string
	Timestamp       time.Time
	Severity        string
	Hash            *string
	Signature       *string
	IsScanned       bool
	CreatedAt       time.Time
}

func getUnscannedFileEvents(db *sql.DB) ([]FileEvent, error) {
	rows, err := db.Query(`SELECT id, agent_id, process_id, process_name, file_path, file_name, event_type, timestamp, severity, file_size, file_hash, file_type, is_scanned, created_at FROM file_events WHERE is_scanned = false`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var events []FileEvent
	for rows.Next() {
		var e FileEvent
		var pid sql.NullInt64
		var pname sql.NullString
		var fsize sql.NullInt64
		var fhash sql.NullString
		var ftype sql.NullString

		if err := rows.Scan(&e.ID, &e.AgentID, &pid, &pname, &e.FilePath, &e.FileName, &e.EventType, &e.Timestamp, &e.Severity, &fsize, &fhash, &ftype, &e.IsScanned, &e.CreatedAt); err != nil {
			return nil, err
		}

		if pid.Valid {
			v := int(pid.Int64)
			e.ProcessID = &v
		} else {
			e.ProcessID = nil
		}

		if pname.Valid {
			s := pname.String
			e.ProcessName = &s
		} else {
			e.ProcessName = nil
		}

		if fsize.Valid {
			v := fsize.Int64
			e.FileSize = &v
		} else {
			e.FileSize = nil
		}

		if fhash.Valid {
			s := fhash.String
			e.FileHash = &s
		} else {
			e.FileHash = nil
		}

		if ftype.Valid {
			s := ftype.String
			e.FileType = &s
		} else {
			e.FileType = nil
		}

		events = append(events, e)
	}
	return events, nil
}

func getUnscannedNetworkEvents(db *sql.DB) ([]NetworkEvent, error) {
	rows, err := db.Query(`SELECT id, agent_id, process_id, process_name, local_ip, local_port, remote_ip, remote_port, protocol, event_type, timestamp, severity, bytes_sent, bytes_received, connection_id, is_scanned, created_at FROM network_events WHERE is_scanned = false`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var events []NetworkEvent
	for rows.Next() {
		var e NetworkEvent
		var pid sql.NullInt64
		var pname sql.NullString
		var rip sql.NullString
		var rport sql.NullInt64
		var bsent sql.NullInt64
		var brecv sql.NullInt64
		var conn sql.NullString

		if err := rows.Scan(&e.ID, &e.AgentID, &pid, &pname, &e.LocalIP, &e.LocalPort, &rip, &rport, &e.Protocol, &e.EventType, &e.Timestamp, &e.Severity, &bsent, &brecv, &conn, &e.IsScanned, &e.CreatedAt); err != nil {
			return nil, err
		}

		if pid.Valid {
			v := int(pid.Int64)
			e.ProcessID = &v
		} else {
			e.ProcessID = nil
		}

		if pname.Valid {
			s := pname.String
			e.ProcessName = &s
		} else {
			e.ProcessName = nil
		}

		if rip.Valid {
			s := rip.String
			e.RemoteIP = &s
		} else {
			e.RemoteIP = nil
		}

		if rport.Valid {
			v := int(rport.Int64)
			e.RemotePort = &v
		} else {
			e.RemotePort = nil
		}

		if bsent.Valid {
			v := bsent.Int64
			e.BytesSent = &v
		} else {
			e.BytesSent = nil
		}

		if brecv.Valid {
			v := brecv.Int64
			e.BytesReceived = &v
		} else {
			e.BytesReceived = nil
		}

		if conn.Valid {
			s := conn.String
			e.ConnectionID = &s
		} else {
			e.ConnectionID = nil
		}

		events = append(events, e)
	}
	return events, nil
}

func getUnscannedProcessEvents(db *sql.DB) ([]ProcessEvent, error) {
	rows, err := db.Query(`SELECT id, agent_id, process_id, parent_process_id, process_name, command_line, executable_path, username, start_time, end_time, cpu_usage, memory_usage, event_type, timestamp, severity, hash, signature, is_scanned, created_at FROM process_events WHERE is_scanned = false`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var events []ProcessEvent
	for rows.Next() {
		var e ProcessEvent
		var procID sql.NullInt64
		var parent sql.NullInt64
		var sTime sql.NullTime
		var eTime sql.NullTime
		var cpu sql.NullFloat64
		var mem sql.NullInt64
		var hash sql.NullString
		var sig sql.NullString
		if err := rows.Scan(&e.ID, &e.AgentID, &procID, &parent, &e.ProcessName, &e.CommandLine, &e.ExecutablePath, &e.Username, &sTime, &eTime, &cpu, &mem, &e.EventType, &e.Timestamp, &e.Severity, &hash, &sig, &e.IsScanned, &e.CreatedAt); err != nil {
			return nil, err
		}

		if procID.Valid {
			e.ProcessID = int(procID.Int64)
		} else {
			e.ProcessID = 0
		}

		if parent.Valid {
			v := int(parent.Int64)
			e.ParentProcessID = &v
		} else {
			e.ParentProcessID = nil
		}

		if sTime.Valid {
			t := sTime.Time
			e.StartTime = &t
		} else {
			e.StartTime = nil
		}

		if eTime.Valid {
			t := eTime.Time
			e.EndTime = &t
		} else {
			e.EndTime = nil
		}

		if cpu.Valid {
			e.CPUUsage = cpu.Float64
		} else {
			e.CPUUsage = 0
		}

		if mem.Valid {
			e.MemoryUsage = mem.Int64
		} else {
			e.MemoryUsage = 0
		}

		if hash.Valid {
			s := hash.String
			e.Hash = &s
		} else {
			e.Hash = nil
		}

		if sig.Valid {
			s := sig.String
			e.Signature = &s
		} else {
			e.Signature = nil
		}

		events = append(events, e)
	}
	return events, nil
}

func checkFileHash(db *sql.DB, hash string) (bool, string) {
	var family, source string
	err := db.QueryRow("SELECT malware_family, source FROM malicious_hashes WHERE sha256_hash = $1", hash).Scan(&family, &source)
	if err == sql.ErrNoRows {
		return false, ""
	} else if err != nil {
		log.Printf("Error checking hash: %v", err)
		return false, ""
	}
	return true, fmt.Sprintf("%s (%s)", family, source)
}

func checkIP(db *sql.DB, ip string) (bool, string) {
	var reason, source string
	err := db.QueryRow("SELECT reason, source FROM malicious_ips WHERE ip_address = $1", ip).Scan(&reason, &source)
	if err == sql.ErrNoRows {
		return false, ""
	} else if err != nil {
		log.Printf("Error checking IP: %v", err)
		return false, ""
	}
	return true, fmt.Sprintf("%s (%s)", reason, source)
}

func checkDomain(db *sql.DB, domain string) (bool, string) {
	var reason, source string
	err := db.QueryRow("SELECT reason, source FROM malicious_domains WHERE domain_name = $1", domain).Scan(&reason, &source)
	if err == sql.ErrNoRows {
		return false, ""
	} else if err != nil {
		log.Printf("Error checking domain: %v", err)
		return false, ""
	}
	return true, fmt.Sprintf("%s (%s)", reason, source)
}

func insertAlert(db *sql.DB, alert Alert) {
	_, err := db.Exec(`INSERT INTO alerts (event_id, indicator, indicator_type, threat_info, severity, status, created_at) VALUES ($1, $2, $3, $4, $5, $6, $7)`,
		alert.EventID, alert.Indicator, alert.IndicatorType, alert.ThreatInfo, alert.Severity, alert.Status, alert.CreatedAt)
	if err != nil {
		log.Printf("Failed to insert alert: %v", err)
	}
}
