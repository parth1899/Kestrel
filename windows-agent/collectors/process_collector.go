package collectors

import (
	"context"
	"fmt"
	"os/exec"
	"strings"
	"sync"
	"time"

	"windows-agent/models"
	"windows-agent/utils"

	"github.com/shirou/gopsutil/v3/process"
	"github.com/sirupsen/logrus"
)

// ProcessCollector collects process-related telemetry data
type ProcessCollector struct {
	agentID        string
	logger         *logrus.Logger
	processChan    chan models.ProcessEvent // Channel for real-time events
	knownProcesses map[int32]bool
	knownMutex     sync.RWMutex
}

// NewProcessCollector creates a new process collector
func NewProcessCollector(agentID string, logger *logrus.Logger) *ProcessCollector {
	return &ProcessCollector{
		agentID:        agentID,
		logger:         logger,
		processChan:    make(chan models.ProcessEvent, 1000),
		knownProcesses: make(map[int32]bool),
	}
}

// StartRealTimeMonitoring starts real-time process monitoring using fast polling
func (pc *ProcessCollector) StartRealTimeMonitoring(ctx context.Context) {
	pc.logger.Info("Starting real-time process monitoring using fast polling")

	// Get initial process list
	processes, err := process.Processes()
	if err != nil {
		pc.logger.Errorf("Failed to get initial process list: %v", err)
		return
	}

	// Populate known processes
	pc.knownMutex.Lock()
	for _, proc := range processes {
		pc.knownProcesses[proc.Pid] = true
	}
	pc.knownMutex.Unlock()

	// Start monitoring loop in a goroutine
	go func() {
		ticker := time.NewTicker(1 * time.Second) // Poll every second
		defer ticker.Stop()
		defer close(pc.processChan) // Close channel when done

		for {
			select {
			case <-ctx.Done():
				pc.logger.Info("Stopping process monitoring")
				return
			case <-ticker.C:
				pc.detectProcessChanges()
			}
		}
	}()
}

// detectProcessChanges detects new and terminated processes
func (pc *ProcessCollector) detectProcessChanges() {
	currentProcesses, err := process.Processes()
	if err != nil {
		pc.logger.Errorf("Failed to get current process list: %v", err)
		return
	}

	// Create a map of current PIDs
	currentPIDs := make(map[int32]bool)
	for _, proc := range currentProcesses {
		currentPIDs[proc.Pid] = true
	}

	pc.knownMutex.Lock()
	defer pc.knownMutex.Unlock()

	// Check for new processes
	for _, proc := range currentProcesses {
		if !pc.knownProcesses[proc.Pid] {
			// This is a new process
			pc.knownProcesses[proc.Pid] = true
			pc.handleProcessStart(proc)
		}
	}

	// Check for terminated processes
	for pid := range pc.knownProcesses {
		if !currentPIDs[pid] {
			// This process has terminated
			delete(pc.knownProcesses, pid)
			pc.handleProcessStop(pid)
		}
	}
}

// handleProcessStart handles process creation events
func (pc *ProcessCollector) handleProcessStart(proc *process.Process) {
	processEvent, err := pc.collectProcessInfo(proc)
	if err != nil {
		pc.logger.Warnf("Failed to collect process info for PID %d: %v", proc.Pid, err)
		return
	}

	processEvent.EventType = "start"
	processEvent.Timestamp = time.Now()
	processEvent.CreatedAt = time.Now()

	// Send to channel for processing
	select {
	case pc.processChan <- *processEvent:
		pc.logger.Debugf("Sent process start event for PID %d", proc.Pid)
	default:
		pc.logger.Warn("Process event channel full, dropping event")
	}
}

// handleProcessStop handles process termination events
func (pc *ProcessCollector) handleProcessStop(pid int32) {
	// Try to get process name from system
	var processName string
	if proc, err := process.NewProcess(pid); err == nil {
		if name, err := proc.Name(); err == nil {
			processName = name
		}
	}

	now := time.Now()
	processEvent := &models.ProcessEvent{
		ID:          utils.GenerateUUID(),
		AgentID:     pc.agentID,
		ProcessID:   int(pid),
		ProcessName: processName,
		EventType:   "stop",
		Timestamp:   now,
		EndTime:     &now,
		Severity:    "low",
		CreatedAt:   now,
	}

	// Send to channel for processing
	select {
	case pc.processChan <- *processEvent:
		pc.logger.Debugf("Sent process stop event for PID %d", pid)
	default:
		pc.logger.Warn("Process event channel full, dropping event")
	}
}

// GetProcessChannel returns the channel for receiving process events
func (pc *ProcessCollector) GetProcessChannel() <-chan models.ProcessEvent {
	return pc.processChan
}

// CollectProcesses collects information about running processes
func (pc *ProcessCollector) CollectProcesses() ([]models.ProcessEvent, error) {
	var events []models.ProcessEvent

	processes, err := process.Processes()
	if err != nil {
		return nil, fmt.Errorf("failed to get processes: %v", err)
	}

	for _, proc := range processes {
		event, err := pc.collectProcessInfo(proc)
		if err != nil {
			pc.logger.Warnf("Failed to collect process info for PID %d: %v", proc.Pid, err)
			continue
		}
		events = append(events, *event)
	}

	pc.logger.Infof("Collected %d process events", len(events))
	return events, nil
}

// collectProcessInfo collects detailed information about a single process
func (pc *ProcessCollector) collectProcessInfo(proc *process.Process) (*models.ProcessEvent, error) {
	event := &models.ProcessEvent{
		ID:        utils.GenerateUUID(),
		AgentID:   pc.agentID,
		ProcessID: int(proc.Pid),
		EventType: "monitor",
		Timestamp: time.Now(),
		Severity:  "info",
		CreatedAt: time.Now(),
	}

	// Get process name
	if name, err := proc.Name(); err == nil {
		event.ProcessName = name
	}

	// Get command line
	if cmdline, err := proc.Cmdline(); err == nil {
		event.CommandLine = cmdline
	}

	// Get executable path
	if exe, err := proc.Exe(); err == nil {
		event.ExecutablePath = exe
	}

	// Get parent process ID
	if ppid, err := proc.Ppid(); err == nil {
		event.ParentProcessID = int(ppid)
	}

	// Get username
	if username, err := proc.Username(); err == nil {
		event.Username = username
	}

	// Get CPU usage
	if cpuPercent, err := proc.CPUPercent(); err == nil {
		event.CPUUsage = cpuPercent
	}

	// Get memory usage
	if memInfo, err := proc.MemoryInfo(); err == nil {
		event.MemoryUsage = memInfo.RSS
	}

	// Get start time
	if createTime, err := proc.CreateTime(); err == nil {
		event.StartTime = time.Unix(createTime/1000, 0)
	}

	// Calculate file hash if executable exists
	if event.ExecutablePath != "" {
		if hash, err := pc.calculateFileHash(event.ExecutablePath); err == nil {
			event.Hash = hash
		}
	}

	// Determine severity based on process characteristics
	event.Severity = pc.determineProcessSeverity(event)

	return event, nil
}

// calculateFileHash calculates SHA256 hash of a file
func (pc *ProcessCollector) calculateFileHash(filePath string) (string, error) {
	// Use PowerShell to calculate SHA256 hash
	cmd := exec.Command("powershell", "-Command",
		fmt.Sprintf("Get-FileHash -Path '%s' -Algorithm SHA256 | Select-Object -ExpandProperty Hash", filePath))

	output, err := cmd.Output()
	if err != nil {
		return "", err
	}

	return strings.TrimSpace(string(output)), nil
}

// determineProcessSeverity determines the severity level of a process
func (pc *ProcessCollector) determineProcessSeverity(event *models.ProcessEvent) string {
	// Check for suspicious process names
	suspiciousNames := []string{
		"cmd.exe", "powershell.exe", "wscript.exe", "cscript.exe", "rundll32.exe",
		"regsvr32.exe", "mshta.exe", "msbuild.exe", "csc.exe", "vbc.exe",
	}

	for _, suspicious := range suspiciousNames {
		if strings.EqualFold(event.ProcessName, suspicious) {
			return "medium"
		}
	}

	// Check for processes running from suspicious locations
	suspiciousPaths := []string{
		"\\temp\\", "\\tmp\\", "\\downloads\\", "\\desktop\\",
	}

	for _, path := range suspiciousPaths {
		if strings.Contains(strings.ToLower(event.ExecutablePath), path) {
			return "medium"
		}
	}

	// Check for high CPU or memory usage
	if event.CPUUsage > 80.0 || event.MemoryUsage > 1000000000 { // 1GB
		return "medium"
	}

	return "low"
}

// CollectProcessStartEvent collects information when a new process starts
func (pc *ProcessCollector) CollectProcessStartEvent(pid int) (*models.ProcessEvent, error) {
	proc, err := process.NewProcess(int32(pid))
	if err != nil {
		return nil, fmt.Errorf("failed to get process %d: %v", pid, err)
	}

	event, err := pc.collectProcessInfo(proc)
	if err != nil {
		return nil, err
	}

	event.EventType = "start"
	event.Severity = "medium" // Process start events are typically medium priority

	return event, nil
}

// CollectProcessStopEvent collects information when a process stops
func (pc *ProcessCollector) CollectProcessStopEvent(pid int, processName string) *models.ProcessEvent {
	now := time.Now()

	return &models.ProcessEvent{
		ID:          utils.GenerateUUID(),
		AgentID:     pc.agentID,
		ProcessID:   pid,
		ProcessName: processName,
		EventType:   "stop",
		Timestamp:   now,
		EndTime:     &now,
		Severity:    "low",
		CreatedAt:   now,
	}
}

// GetProcessCount returns the total number of running processes
func (pc *ProcessCollector) GetProcessCount() (int, error) {
	processes, err := process.Processes()
	if err != nil {
		return 0, err
	}
	return len(processes), nil
}

// GetProcessesByUser returns processes running under a specific user
func (pc *ProcessCollector) GetProcessesByUser(username string) ([]models.ProcessEvent, error) {
	var events []models.ProcessEvent

	processes, err := process.Processes()
	if err != nil {
		return nil, err
	}

	for _, proc := range processes {
		if procUsername, err := proc.Username(); err == nil && procUsername == username {
			event, err := pc.collectProcessInfo(proc)
			if err != nil {
				continue
			}
			events = append(events, *event)
		}
	}

	return events, nil
}
