package collectors

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"windows-agent/models"
	"windows-agent/utils"

	"github.com/fsnotify/fsnotify"
	"github.com/sirupsen/logrus"
)

// FileCollector collects file-related telemetry data
type FileCollector struct {
	agentID  string
	logger   *logrus.Logger
	watcher  *fsnotify.Watcher
	fileChan chan models.FileEvent // Channel for real-time events
	// Track recently seen files to avoid duplicates
	recentFiles map[string]time.Time
}

// NewFileCollector creates a new file collector
func NewFileCollector(agentID string, logger *logrus.Logger) (*FileCollector, error) {
	watcher, err := fsnotify.NewWatcher()
	if err != nil {
		return nil, fmt.Errorf("failed to create file watcher: %v", err)
	}

	return &FileCollector{
		agentID:     agentID,
		logger:      logger,
		watcher:     watcher,
		fileChan:    make(chan models.FileEvent, 1000),
		recentFiles: make(map[string]time.Time),
	}, nil
}

// StartRealTimeMonitoring starts real-time file monitoring
func (fc *FileCollector) StartRealTimeMonitoring(ctx context.Context) error {
	fc.logger.Info("Starting real-time file monitoring")

	// Watch common directories
	directories := []string{
		os.Getenv("TEMP"),
		os.Getenv("TMP"),
		os.Getenv("USERPROFILE") + "\\Downloads",
		os.Getenv("USERPROFILE") + "\\Desktop",
		os.Getenv("USERPROFILE") + "\\Documents",
	}

	for _, dir := range directories {
		if dir == "" {
			continue
		}
		if err := fc.watcher.Add(dir); err != nil {
			fc.logger.Warnf("Failed to watch directory %s: %v", dir, err)
		} else {
			fc.logger.Debugf("Watching directory: %s", dir)
		}
	}

	go fc.watchLoop(ctx)
	return nil
}

// watchLoop handles file system events
func (fc *FileCollector) watchLoop(ctx context.Context) {
	defer close(fc.fileChan)
	defer fc.watcher.Close()

	for {
		select {
		case <-ctx.Done():
			fc.logger.Info("Stopping file monitoring")
			return

		case event, ok := <-fc.watcher.Events:
			if !ok {
				return
			}
			fc.handleFileEvent(event)

		case err, ok := <-fc.watcher.Errors:
			if !ok {
				return
			}
			fc.logger.Errorf("File watcher error: %v", err)
		}
	}
}

// handleFileEvent processes file system events
func (fc *FileCollector) handleFileEvent(event fsnotify.Event) {
	// Skip directories and system files
	if info, err := os.Stat(event.Name); err != nil || info.IsDir() || fc.shouldSkipFile(event.Name, info) {
		return
	}

	// Debounce: skip recently processed files
	if fc.isRecentlySeen(event.Name, time.Now()) {
		return
	}

	info, err := os.Stat(event.Name)
	if err != nil {
		fc.logger.Debugf("Failed to stat file %s: %v", event.Name, err)
		return
	}

	// Determine event type
	eventType := "modify"
	if event.Op.Has(fsnotify.Create) {
		eventType = "create"
	} else if event.Op.Has(fsnotify.Remove) || event.Op.Has(fsnotify.Rename) {
		eventType = "delete"
	} else if event.Op.Has(fsnotify.Write) {
		eventType = "modify"
	}

	fileEvent := fc.createFileEvent(event.Name, info, time.Now())
	fileEvent.EventType = eventType

	// Mark as recently seen
	fc.recentFiles[event.Name] = time.Now()

	// Send to channel
	select {
	case fc.fileChan <- *fileEvent:
		fc.logger.Debugf("Sent file event: %s %s", eventType, event.Name)
	default:
		fc.logger.Warn("File event channel full, dropping event")
	}
}

// GetFileChannel returns the channel for receiving file events
func (fc *FileCollector) GetFileChannel() <-chan models.FileEvent {
	return fc.fileChan
}

// CleanupOldEntries removes old entries from the recent files map
func (fc *FileCollector) CleanupOldEntries() {
	cutoff := time.Now().Add(-10 * time.Minute)
	for path, lastSeen := range fc.recentFiles {
		if lastSeen.Before(cutoff) {
			delete(fc.recentFiles, path)
		}
	}
}

// CollectFileEvents scans for file system changes and creates events
func (fc *FileCollector) CollectFileEvents() ([]models.FileEvent, error) {
	var events []models.FileEvent
	now := time.Now()

	// Scan common directories for changes
	directories := []string{
		os.Getenv("TEMP"),
		os.Getenv("TMP"),
		os.Getenv("USERPROFILE") + "\\Downloads",
		os.Getenv("USERPROFILE") + "\\Desktop",
		os.Getenv("USERPROFILE") + "\\Documents",
	}

	for _, dir := range directories {
		if dir == "" {
			continue
		}

		dirEvents, err := fc.scanDirectory(dir, now)
		if err != nil {
			fc.logger.Warnf("Failed to scan directory %s: %v", dir, err)
			continue
		}
		events = append(events, dirEvents...)
	}

	fc.logger.Infof("Collected %d file events", len(events))
	return events, nil
}

// scanDirectory scans a directory for file changes
func (fc *FileCollector) scanDirectory(dirPath string, scanTime time.Time) ([]models.FileEvent, error) {
	var events []models.FileEvent

	err := filepath.Walk(dirPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil // Skip files we can't access
		}

		// Skip directories and system files
		if info.IsDir() || fc.shouldSkipFile(path, info) {
			return nil
		}

		// Check if we've seen this file recently (within last 5 minutes)
		if fc.isRecentlySeen(path, scanTime) {
			return nil
		}

		// Create file event
		event := fc.createFileEvent(path, info, scanTime)
		events = append(events, *event)

		// Mark as recently seen
		fc.recentFiles[path] = scanTime

		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("error walking directory %s: %v", dirPath, err)
	}

	return events, nil
}

// shouldSkipFile determines if a file should be skipped
func (fc *FileCollector) shouldSkipFile(path string, info os.FileInfo) bool {
	// Skip system and hidden files (Windows doesn't have os.ModeHidden)
	// We'll skip based on other criteria instead

	// Skip files with certain extensions
	skipExtensions := []string{".tmp", ".log", ".bak", ".old", ".cache"}
	ext := strings.ToLower(filepath.Ext(path))
	for _, skipExt := range skipExtensions {
		if ext == skipExt {
			return true
		}
	}

	// Skip files in system directories
	lowerPath := strings.ToLower(path)
	systemDirs := []string{"\\windows\\", "\\program files\\", "\\programdata\\"}
	for _, sysDir := range systemDirs {
		if strings.Contains(lowerPath, sysDir) {
			return true
		}
	}

	return false
}

// isRecentlySeen checks if a file was recently processed
func (fc *FileCollector) isRecentlySeen(path string, currentTime time.Time) bool {
	if lastSeen, exists := fc.recentFiles[path]; exists {
		return currentTime.Sub(lastSeen) < 5*time.Minute
	}
	return false
}

// createFileEvent creates a FileEvent from file information
func (fc *FileCollector) createFileEvent(path string, info os.FileInfo, timestamp time.Time) *models.FileEvent {
	event := &models.FileEvent{
		ID:        utils.GenerateUUID(),
		AgentID:   fc.agentID,
		FilePath:  path,
		FileName:  info.Name(),
		EventType: "monitor",
		Timestamp: timestamp,
		Severity:  fc.determineFileSeverity(path, info),
		FileSize:  info.Size(),
		FileType:  strings.ToLower(filepath.Ext(path)),
		CreatedAt: timestamp,
	}

	// Try to get file hash (this might be slow for large files)
	if info.Size() < 100*1024*1024 { // Only hash files smaller than 100MB
		if hash, err := fc.calculateFileHash(path); err == nil {
			event.FileHash = hash
		}
	}

	return event
}

// determineFileSeverity determines the severity level of a file
func (fc *FileCollector) determineFileSeverity(path string, info os.FileInfo) string {
	lowerPath := strings.ToLower(path)

	// High severity - suspicious locations
	suspiciousPaths := []string{
		"\\temp\\", "\\tmp\\", "\\downloads\\", "\\desktop\\",
		"\\appdata\\local\\temp\\", "\\appdata\\roaming\\temp\\",
	}

	for _, suspicious := range suspiciousPaths {
		if strings.Contains(lowerPath, suspicious) {
			return "medium"
		}
	}

	// High severity - suspicious extensions
	suspiciousExtensions := []string{".exe", ".bat", ".cmd", ".ps1", ".vbs", ".js"}
	ext := strings.ToLower(filepath.Ext(path))
	for _, suspicious := range suspiciousExtensions {
		if ext == suspicious {
			return "medium"
		}
	}

	// Check file size (very large files might be suspicious)
	if info.Size() > 500*1024*1024 { // 500MB
		return "medium"
	}

	return "low"
}

// calculateFileHash calculates SHA256 hash of a file
func (fc *FileCollector) calculateFileHash(filePath string) (string, error) {
	// For now, return a placeholder hash
	// In production, you'd implement actual file hashing
	return fmt.Sprintf("hash_%s_%d", filepath.Base(filePath), time.Now().Unix()), nil
}

// CollectFileAccessEvent creates an event when a file is accessed
func (fc *FileCollector) CollectFileAccessEvent(filePath string, accessType string) *models.FileEvent {
	info, err := os.Stat(filePath)
	if err != nil {
		fc.logger.Warnf("Failed to get file info for %s: %v", filePath, err)
		return nil
	}

	event := fc.createFileEvent(filePath, info, time.Now())
	event.EventType = accessType
	event.Severity = "medium" // File access events are typically medium priority

	return event
}

// GetFileCount returns the number of files being monitored
func (fc *FileCollector) GetFileCount() int {
	return len(fc.recentFiles)
}
