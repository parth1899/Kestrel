package database

import (
	"database/sql"
	"fmt"
	"log"
	"time"

	"windows-agent/config"

	// use pgx stdlib to improve compatibility with pooled Postgres (Neon/pgbouncer)
	_ "github.com/jackc/pgx/v5/stdlib"
)

type PostgresDB struct {
	DB *sql.DB
}

// NewPostgresDB creates a new PostgreSQL database connection
func NewPostgresDB(config *config.DatabaseConfig) (*PostgresDB, error) {
	// Use simple protocol to avoid server-side prepared statement caching issues
	psqlInfo := fmt.Sprintf("host=%s port=%d user=%s password=%s dbname=%s sslmode=%s prefer_simple_protocol=true",
		config.Host, config.Port, config.User, config.Password, config.DBName, config.SSLMode)

	// use pgx driver registered by github.com/jackc/pgx/v5/stdlib
	db, err := sql.Open("pgx", psqlInfo)
	if err != nil {
		return nil, fmt.Errorf("error opening database: %v", err)
	}

	// Test the connection
	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("error connecting to database: %v", err)
	}

	// Set connection pool settings
	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(25)
	db.SetConnMaxLifetime(5 * time.Minute)

	return &PostgresDB{DB: db}, nil
}

// Close closes the database connection
func (p *PostgresDB) Close() error {
	return p.DB.Close()
}

// InitTables creates all necessary tables if they don't exist
func (p *PostgresDB) InitTables() error {
	queries := []string{
		`CREATE TABLE IF NOT EXISTS telemetry_events (
	       id VARCHAR(255) PRIMARY KEY,
	       agent_id VARCHAR(255) NOT NULL,
	       event_type VARCHAR(100) NOT NULL,
	       timestamp TIMESTAMP NOT NULL,
	       severity VARCHAR(50) NOT NULL,
	       data JSONB,
	       processed BOOLEAN DEFAULT FALSE,
	       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	       )`,
		`CREATE TABLE IF NOT EXISTS alerts (
	       id SERIAL PRIMARY KEY,
	       event_id VARCHAR(255) NOT NULL,
	       indicator VARCHAR(255) NOT NULL,
	       indicator_type VARCHAR(100) NOT NULL,
	       threat_info TEXT,
	       severity VARCHAR(50) NOT NULL,
	       status VARCHAR(50) NOT NULL,
	       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	       )`,
		`CREATE TABLE IF NOT EXISTS process_events (
			   id VARCHAR(255) PRIMARY KEY,
			   agent_id VARCHAR(255) NOT NULL,
			   process_id INTEGER NOT NULL,
			   parent_process_id INTEGER,
			   process_name VARCHAR(500) NOT NULL,
			   command_line TEXT,
			   executable_path VARCHAR(1000),
			   username VARCHAR(255),
			   start_time TIMESTAMP,
			   end_time TIMESTAMP,
			   cpu_usage DECIMAL(10,2),
			   memory_usage BIGINT,
			   event_type VARCHAR(100) NOT NULL,
			   timestamp TIMESTAMP NOT NULL,
			   severity VARCHAR(50) NOT NULL,
			   hash VARCHAR(255),
			   signature TEXT,
			   is_scanned BOOLEAN DEFAULT FALSE,
			   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		   )`,
		`CREATE TABLE IF NOT EXISTS file_events (
			   id VARCHAR(255) PRIMARY KEY,
			   agent_id VARCHAR(255) NOT NULL,
			   process_id INTEGER,
			   process_name VARCHAR(500),
			   file_path VARCHAR(1000) NOT NULL,
			   file_name VARCHAR(500) NOT NULL,
			   event_type VARCHAR(100) NOT NULL,
			   timestamp TIMESTAMP NOT NULL,
			   severity VARCHAR(50) NOT NULL,
			   file_size BIGINT,
			   file_hash VARCHAR(255),
			   file_type VARCHAR(100),
			   is_scanned BOOLEAN DEFAULT FALSE,
			   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		   )`,
		`CREATE TABLE IF NOT EXISTS network_events (
			   id VARCHAR(255) PRIMARY KEY,
			   agent_id VARCHAR(255) NOT NULL,
			   process_id INTEGER,
			   process_name VARCHAR(500),
			   local_ip VARCHAR(45) NOT NULL,
			   local_port INTEGER NOT NULL,
			   remote_ip VARCHAR(45),
			   remote_port INTEGER,
			   protocol VARCHAR(10) NOT NULL,
			   event_type VARCHAR(100) NOT NULL,
			   timestamp TIMESTAMP NOT NULL,
			   severity VARCHAR(50) NOT NULL,
			   bytes_sent BIGINT,
			   bytes_received BIGINT,
			   connection_id VARCHAR(255),
			   is_scanned BOOLEAN DEFAULT FALSE,
			   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		   )`,
		`CREATE TABLE IF NOT EXISTS system_info (
			id VARCHAR(255) PRIMARY KEY,
			agent_id VARCHAR(255) NOT NULL,
			hostname VARCHAR(255) NOT NULL,
			os_version VARCHAR(255) NOT NULL,
			architecture VARCHAR(50) NOT NULL,
			total_memory BIGINT NOT NULL,
			available_memory BIGINT NOT NULL,
			cpu_count INTEGER NOT NULL,
			cpu_usage DECIMAL(10,2) NOT NULL,
			disk_usage DECIMAL(10,2) NOT NULL,
			uptime BIGINT NOT NULL,
			timestamp TIMESTAMP NOT NULL,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)`,
		`CREATE TABLE IF NOT EXISTS threat_indicators (
			id VARCHAR(255) PRIMARY KEY,
			agent_id VARCHAR(255) NOT NULL,
			event_id VARCHAR(255) NOT NULL,
			event_type VARCHAR(100) NOT NULL,
			threat_type VARCHAR(100) NOT NULL,
			description TEXT NOT NULL,
			confidence DECIMAL(5,2) NOT NULL,
			severity VARCHAR(50) NOT NULL,
			timestamp TIMESTAMP NOT NULL,
			status VARCHAR(50) DEFAULT 'new',
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)`,
	}

	for _, query := range queries {
		if _, err := p.DB.Exec(query); err != nil {
			return fmt.Errorf("error creating table: %v", err)
		}
	}

	log.Println("Database tables initialized successfully")

	// Log prepared statements and active sessions for diagnostics (Neon/pgbouncer can cache prepared statements)
	p.LogPreparedStatements()
	return nil
}

// LogPreparedStatements logs prepared statements and active sessions for debugging
func (p *PostgresDB) LogPreparedStatements() {
	// prepared statements
	rows, err := p.DB.Query("SELECT name, statement, prepare_time FROM pg_prepared_statements")
	if err != nil {
		log.Printf("could not query pg_prepared_statements: %v", err)
	} else {
		defer rows.Close()
		for rows.Next() {
			var name, stmt string
			var t time.Time
			if err := rows.Scan(&name, &stmt, &t); err != nil {
				log.Printf("error scanning prepared statement row: %v", err)
				continue
			}
			log.Printf("prepared_statement: name=%s time=%s stmt=%s", name, t.Format(time.RFC3339), stmt)
		}
	}

	// active sessions
	sarows, err := p.DB.Query("SELECT pid, usename, application_name, state, query FROM pg_stat_activity WHERE datname = current_database()")
	if err != nil {
		log.Printf("could not query pg_stat_activity: %v", err)
		return
	}
	defer sarows.Close()
	for sarows.Next() {
		var pid int
		var usename, appname, state, queryText string
		if err := sarows.Scan(&pid, &usename, &appname, &state, &queryText); err != nil {
			log.Printf("error scanning pg_stat_activity row: %v", err)
			continue
		}
		log.Printf("pg_stat_activity: pid=%d user=%s app=%s state=%s query=%s", pid, usename, appname, state, queryText)
	}
}

// CreateIndexes creates indexes for better query performance
func (p *PostgresDB) CreateIndexes() error {
	indexes := []string{
		"CREATE INDEX IF NOT EXISTS idx_telemetry_events_agent_id ON telemetry_events(agent_id)",
		"CREATE INDEX IF NOT EXISTS idx_telemetry_events_timestamp ON telemetry_events(timestamp)",
		"CREATE INDEX IF NOT EXISTS idx_telemetry_events_event_type ON telemetry_events(event_type)",
		"CREATE INDEX IF NOT EXISTS idx_process_events_agent_id ON process_events(agent_id)",
		"CREATE INDEX IF NOT EXISTS idx_process_events_timestamp ON process_events(timestamp)",
		"CREATE INDEX IF NOT EXISTS idx_process_events_process_id ON process_events(process_id)",
		"CREATE INDEX IF NOT EXISTS idx_file_events_agent_id ON file_events(agent_id)",
		"CREATE INDEX IF NOT EXISTS idx_file_events_timestamp ON file_events(timestamp)",
		"CREATE INDEX IF NOT EXISTS idx_file_events_file_path ON file_events(file_path)",
		"CREATE INDEX IF NOT EXISTS idx_network_events_agent_id ON network_events(agent_id)",
		"CREATE INDEX IF NOT EXISTS idx_network_events_timestamp ON network_events(timestamp)",
		"CREATE INDEX IF NOT EXISTS idx_network_events_remote_ip ON network_events(remote_ip)",
		"CREATE INDEX IF NOT EXISTS idx_system_info_agent_id ON system_info(agent_id)",
		"CREATE INDEX IF NOT EXISTS idx_system_info_timestamp ON system_info(timestamp)",
		"CREATE INDEX IF NOT EXISTS idx_threat_indicators_agent_id ON threat_indicators(agent_id)",
		"CREATE INDEX IF NOT EXISTS idx_threat_indicators_timestamp ON threat_indicators(timestamp)",
		"CREATE INDEX IF NOT EXISTS idx_threat_indicators_status ON threat_indicators(status)",
	}

	for _, index := range indexes {
		if _, err := p.DB.Exec(index); err != nil {
			return fmt.Errorf("error creating index: %v", err)
		}
	}

	log.Println("Database indexes created successfully")
	return nil
}
