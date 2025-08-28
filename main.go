package main

import (
	"fmt"
	"os"
	"os/signal"
	"syscall"

	"windows-agent/config"
	"windows-agent/database"
	"windows-agent/services"

	"github.com/sirupsen/logrus"
)

func main() {
	// Initialize logger
	logger := logrus.New()
	logger.SetLevel(logrus.InfoLevel)
	logger.SetFormatter(&logrus.TextFormatter{
		FullTimestamp: true,
	})

	logger.Info("Starting Windows Security Agent...")

	// Load configuration
	cfg, err := config.LoadConfig()
	if err != nil {
		logger.Fatalf("Failed to load configuration: %v", err)
	}

	// Set log level from config
	if level, err := logrus.ParseLevel(cfg.Agent.LogLevel); err == nil {
		logger.SetLevel(level)
	}

	logger.Infof("Configuration loaded: Agent ID=%s, DB=%s:%d",
		cfg.Agent.ID, cfg.Database.Host, cfg.Database.Port)

	// Initialize database connection
	db, err := database.NewPostgresDB(&cfg.Database)
	if err != nil {
		logger.Fatalf("Failed to connect to database: %v", err)
	}
	defer db.Close()

	// Initialize database tables and indexes
	if err := db.InitTables(); err != nil {
		logger.Fatalf("Failed to initialize database tables: %v", err)
	}

	if err := db.CreateIndexes(); err != nil {
		logger.Fatalf("Failed to create database indexes: %v", err)
	}

	// Initialize repository
	repo := database.NewRepository(db)

	// Initialize telemetry service
	telemetryService := services.NewTelemetryService(cfg, repo, logger)

	// Start telemetry service
	if err := telemetryService.Start(); err != nil {
		logger.Fatalf("Failed to start telemetry service: %v", err)
	}

	// Set up signal handling for graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	logger.Info("Windows Security Agent is running. Press Ctrl+C to stop.")

	// Wait for shutdown signal
	<-sigChan
	logger.Info("Shutdown signal received. Stopping agent...")

	// Stop telemetry service
	if err := telemetryService.Stop(); err != nil {
		logger.Errorf("Error stopping telemetry service: %v", err)
	}

	logger.Info("Windows Security Agent stopped successfully")
}

// setupGracefulShutdown sets up graceful shutdown handling
func setupGracefulShutdown(telemetryService *services.TelemetryService, logger *logrus.Logger) {
	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)

	go func() {
		<-c
		logger.Info("Received shutdown signal, starting graceful shutdown...")

		// Stop telemetry service
		if err := telemetryService.Stop(); err != nil {
			logger.Errorf("Error stopping telemetry service: %v", err)
		}

		logger.Info("Graceful shutdown completed")
		os.Exit(0)
	}()
}

// printStartupBanner prints the agent startup banner
func printStartupBanner() {
	fmt.Println(`
╔══════════════════════════════════════════════════════════════╗
║                    Windows Security Agent                    ║
║                        Version 1.0.0                        ║
║                                                              ║
║  Enterprise-grade endpoint security monitoring platform      ║
║  Collecting process, system, and network telemetry data     ║
╚══════════════════════════════════════════════════════════════╝
`)
}
