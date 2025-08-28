package services

import (
	"fmt"
	"sync"
	"time"

	"windows-agent/collectors"
	"windows-agent/config"
	"windows-agent/database"
	"windows-agent/models"

	"github.com/sirupsen/logrus"
)

// TelemetryService orchestrates data collection and storage
type TelemetryService struct {
	config           *config.Config
	repo             *database.Repository
	processCollector *collectors.ProcessCollector
	systemCollector  *collectors.SystemCollector
	fileCollector    *collectors.FileCollector
	networkCollector *collectors.NetworkCollector
	logger           *logrus.Logger
	stopChan         chan struct{}
	wg               sync.WaitGroup
	running          bool
	mutex            sync.RWMutex
}

// NewTelemetryService creates a new telemetry service
func NewTelemetryService(cfg *config.Config, repo *database.Repository, logger *logrus.Logger) *TelemetryService {
	return &TelemetryService{
		config:           cfg,
		repo:             repo,
		processCollector: collectors.NewProcessCollector(cfg.Agent.ID, logger),
		systemCollector:  collectors.NewSystemCollector(cfg.Agent.ID, logger),
		fileCollector:    collectors.NewFileCollector(cfg.Agent.ID, logger),
		networkCollector: collectors.NewNetworkCollector(cfg.Agent.ID, logger),
		logger:           logger,
		stopChan:         make(chan struct{}),
	}
}

// Start begins the telemetry collection service
func (ts *TelemetryService) Start() error {
	ts.mutex.Lock()
	defer ts.mutex.Unlock()

	if ts.running {
		return fmt.Errorf("telemetry service is already running")
	}

	ts.running = true
	ts.logger.Info("Starting telemetry service...")

	// Start background collection
	ts.wg.Add(1)
	go ts.collectionLoop()

	// Start system monitoring
	ts.wg.Add(1)
	go ts.systemMonitoringLoop()

	ts.logger.Info("Telemetry service started successfully")
	return nil
}

// Stop stops the telemetry collection service
func (ts *TelemetryService) Stop() error {
	ts.mutex.Lock()
	defer ts.mutex.Unlock()

	if !ts.running {
		return fmt.Errorf("telemetry service is not running")
	}

	ts.logger.Info("Stopping telemetry service...")
	close(ts.stopChan)
	ts.running = false

	// Wait for all goroutines to finish
	ts.wg.Wait()
	ts.logger.Info("Telemetry service stopped successfully")
	return nil
}

// IsRunning returns whether the service is currently running
func (ts *TelemetryService) IsRunning() bool {
	ts.mutex.RLock()
	defer ts.mutex.RUnlock()
	return ts.running
}

// collectionLoop runs the main collection loop
func (ts *TelemetryService) collectionLoop() {
	defer ts.wg.Done()

	ticker := time.NewTicker(time.Duration(ts.config.Agent.CollectorInterval) * time.Second)
	defer ticker.Stop()

	ts.logger.Infof("Starting collection loop with interval: %d seconds", ts.config.Agent.CollectorInterval)

	for {
		select {
		case <-ts.stopChan:
			ts.logger.Info("Collection loop stopped")
			return
		case <-ticker.C:
			if err := ts.collectAndStore(); err != nil {
				ts.logger.Errorf("Error in collection cycle: %v", err)
			}
		}
	}
}

// systemMonitoringLoop runs system monitoring at a different interval
func (ts *TelemetryService) systemMonitoringLoop() {
	defer ts.wg.Done()

	ticker := time.NewTicker(5 * time.Minute) // System info every 5 minutes
	defer ticker.Stop()

	ts.logger.Info("Starting system monitoring loop")

	// Collect system info immediately on startup
	if err := ts.collectSystemInfo(); err != nil {
		ts.logger.Errorf("Error collecting initial system info: %v", err)
	}

	for {
		select {
		case <-ts.stopChan:
			ts.logger.Info("System monitoring loop stopped")
			return
		case <-ticker.C:
			if err := ts.collectSystemInfo(); err != nil {
				ts.logger.Errorf("Error collecting system info: %v", err)
			}
		}
	}
}

// collectAndStore performs a complete collection cycle
func (ts *TelemetryService) collectAndStore() error {
	ts.logger.Debug("Starting collection cycle")

	// Collect process information
	processEvents, err := ts.processCollector.CollectProcesses()
	if err != nil {
		ts.logger.Errorf("Failed to collect process events: %v", err)
	} else {
		ts.logger.Debugf("Collected %d process events", len(processEvents))
	}

	// Store process events
	for _, event := range processEvents {
		if err := ts.repo.SaveProcessEvent(&event); err != nil {
			ts.logger.Errorf("Failed to save process event: %v", err)
		}
	}

	// Collect file events
	fileEvents, err := ts.fileCollector.CollectFileEvents()
	if err != nil {
		ts.logger.Errorf("Failed to collect file events: %v", err)
	} else {
		ts.logger.Debugf("Collected %d file events", len(fileEvents))
	}

	// Store file events
	for _, event := range fileEvents {
		if err := ts.repo.SaveFileEvent(&event); err != nil {
			ts.logger.Errorf("Failed to save file event: %v", err)
		}
	}

	// Collect network events
	networkEvents, err := ts.networkCollector.CollectNetworkEvents()
	if err != nil {
		ts.logger.Errorf("Failed to collect network events: %v", err)
	} else {
		ts.logger.Debugf("Collected %d network events", len(networkEvents))
	}

	// Store network events
	for _, event := range networkEvents {
		if err := ts.repo.SaveNetworkEvent(&event); err != nil {
			ts.logger.Errorf("Failed to save network event: %v", err)
		}
	}

	// Collect and store performance metrics
	if err := ts.collectPerformanceMetrics(); err != nil {
		ts.logger.Errorf("Failed to collect performance metrics: %v", err)
	}

	ts.logger.Debug("Collection cycle completed")
	return nil
}

// collectSystemInfo collects and stores system information
func (ts *TelemetryService) collectSystemInfo() error {
	ts.logger.Debug("Collecting system information")

	systemInfo, err := ts.systemCollector.CollectSystemInfo()
	if err != nil {
		return fmt.Errorf("failed to collect system info: %v", err)
	}

	if err := ts.repo.SaveSystemInfo(systemInfo); err != nil {
		return fmt.Errorf("failed to save system info: %v", err)
	}

	ts.logger.Debugf("System info collected and stored for host: %s", systemInfo.Hostname)
	return nil
}

// collectSystemInfoOnDemand performs immediate system info collection
func (ts *TelemetryService) collectSystemInfoOnDemand() error {
	ts.logger.Info("Performing on-demand system info collection")
	return ts.collectSystemInfo()
}

// collectPerformanceMetrics collects and stores performance metrics
func (ts *TelemetryService) collectPerformanceMetrics() error {
	ts.logger.Debug("Collecting performance metrics")

	metrics, err := ts.systemCollector.CollectPerformanceMetrics()
	if err != nil {
		return fmt.Errorf("failed to collect performance metrics: %v", err)
	}

	// Create a telemetry event for performance metrics
	event := &models.TelemetryEvent{
		ID:        ts.generateEventID("perf"),
		AgentID:   ts.config.Agent.ID,
		EventType: "performance_metrics",
		Timestamp: time.Now(),
		Severity:  "info",
		Data:      metrics,
		Processed: false,
		CreatedAt: time.Now(),
	}

	if err := ts.repo.SaveTelemetryEvent(event); err != nil {
		return fmt.Errorf("failed to save performance metrics: %v", err)
	}

	ts.logger.Debug("Performance metrics collected and stored")
	return nil
}

// generateEventID generates a unique event ID
func (ts *TelemetryService) generateEventID(prefix string) string {
	return fmt.Sprintf("%s-%s-%d", prefix, ts.config.Agent.ID, time.Now().UnixNano())
}

// CollectOnDemand performs an immediate collection cycle
func (ts *TelemetryService) CollectOnDemand() error {
	ts.logger.Info("Performing on-demand collection")
	return ts.collectAndStore()
}

// GetCollectionStats returns statistics about the collection service
func (ts *TelemetryService) GetCollectionStats() (map[string]interface{}, error) {
	stats := make(map[string]interface{})

	// Get event counts for the last hour
	since := time.Now().Add(-1 * time.Hour)

	if count, err := ts.repo.GetEventCount(ts.config.Agent.ID, "process", since); err == nil {
		stats["process_events_last_hour"] = count
	}

	if count, err := ts.repo.GetEventCount(ts.config.Agent.ID, "performance_metrics", since); err == nil {
		stats["performance_events_last_hour"] = count
	}

	// Get latest system info
	if systemInfo, err := ts.repo.GetLatestSystemInfo(ts.config.Agent.ID); err == nil && systemInfo != nil {
		stats["last_system_info"] = systemInfo.Timestamp
		stats["system_health"] = map[string]interface{}{
			"cpu_usage":    systemInfo.CPUUsage,
			"memory_usage": float64(systemInfo.TotalMemory-systemInfo.AvailableMemory) / float64(systemInfo.TotalMemory) * 100,
			"disk_usage":   systemInfo.DiskUsage,
		}
	}

	stats["service_running"] = ts.IsRunning()
	stats["collection_interval"] = ts.config.Agent.CollectorInterval
	stats["last_collection"] = time.Now()

	return stats, nil
}

// CollectSpecificData collects specific types of data on demand
func (ts *TelemetryService) CollectSpecificData(dataType string) error {
	switch dataType {
	case "processes":
		return ts.collectProcessData()
	case "system":
		return ts.collectSystemInfo()
	case "performance":
		return ts.collectPerformanceMetrics()
	case "files":
		return ts.collectFileData()
	case "network":
		return ts.collectNetworkData()
	case "all":
		return ts.collectAndStore()
	default:
		return fmt.Errorf("unknown data type: %s", dataType)
	}
}

// collectProcessData collects only process-related data
func (ts *TelemetryService) collectProcessData() error {
	ts.logger.Info("Collecting process data on demand")

	processEvents, err := ts.processCollector.CollectProcesses()
	if err != nil {
		return fmt.Errorf("failed to collect process events: %v", err)
	}

	for _, event := range processEvents {
		if err := ts.repo.SaveProcessEvent(&event); err != nil {
			ts.logger.Errorf("Failed to save process event: %v", err)
		}
	}

	ts.logger.Infof("Collected and stored %d process events", len(processEvents))
	return nil
}

// GetSystemHealth returns the current system health score
func (ts *TelemetryService) GetSystemHealth() (float64, error) {
	return ts.systemCollector.GetSystemHealth()
}

// GetProcessCount returns the current number of running processes
func (ts *TelemetryService) GetProcessCount() (int, error) {
	return ts.processCollector.GetProcessCount()
}

// collectFileData collects only file-related data
func (ts *TelemetryService) collectFileData() error {
	ts.logger.Info("Collecting file data on demand")

	fileEvents, err := ts.fileCollector.CollectFileEvents()
	if err != nil {
		return fmt.Errorf("failed to collect file events: %v", err)
	}

	for _, event := range fileEvents {
		if err := ts.repo.SaveFileEvent(&event); err != nil {
			ts.logger.Errorf("Failed to save file event: %v", err)
		}
	}

	ts.logger.Infof("Collected and stored %d file events", len(fileEvents))
	return nil
}

// collectNetworkData collects only network-related data
func (ts *TelemetryService) collectNetworkData() error {
	ts.logger.Info("Collecting network data on demand")

	networkEvents, err := ts.networkCollector.CollectNetworkEvents()
	if err != nil {
		return fmt.Errorf("failed to collect network events: %v", err)
	}

	for _, event := range networkEvents {
		if err := ts.repo.SaveNetworkEvent(&event); err != nil {
			ts.logger.Errorf("Failed to save network event: %v", err)
		}
	}

	ts.logger.Infof("Collected and stored %d network events", len(networkEvents))
	return nil
}
