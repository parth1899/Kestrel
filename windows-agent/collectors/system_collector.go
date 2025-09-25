package collectors

import (
	"fmt"
	"os"
	"runtime"
	"strings"
	"time"

	"windows-agent/models"
	"windows-agent/utils"

	"github.com/shirou/gopsutil/v3/cpu"
	"github.com/shirou/gopsutil/v3/disk"
	"github.com/shirou/gopsutil/v3/host"
	"github.com/shirou/gopsutil/v3/mem"
	"github.com/sirupsen/logrus"
)

// SystemCollector collects system-level telemetry data
type SystemCollector struct {
	agentID string
	logger  *logrus.Logger
}

// NewSystemCollector creates a new system collector
func NewSystemCollector(agentID string, logger *logrus.Logger) *SystemCollector {
	return &SystemCollector{
		agentID: agentID,
		logger:  logger,
	}
}

// CollectSystemInfo collects comprehensive system information
func (sc *SystemCollector) CollectSystemInfo() (*models.SystemInfo, error) {
	info := &models.SystemInfo{
		ID:        utils.GenerateUUID(),
		AgentID:   sc.agentID,
		Timestamp: time.Now(),
		CreatedAt: time.Now(),
	}

	// Get hostname
	if hostname, err := os.Hostname(); err == nil {
		info.Hostname = hostname
	}

	// Get OS version and architecture
	info.OSVersion = runtime.GOOS + " " + runtime.GOARCH
	info.Architecture = runtime.GOARCH

	// Get memory information
	if memInfo, err := mem.VirtualMemory(); err == nil {
		info.TotalMemory = memInfo.Total
		info.AvailableMemory = memInfo.Available
	}

	// Get CPU information
	if cpuCount, err := cpu.Counts(false); err == nil {
		info.CPUCount = cpuCount
	}

	// Get CPU usage
	if cpuPercent, err := cpu.Percent(0, false); err == nil && len(cpuPercent) > 0 {
		info.CPUUsage = cpuPercent[0]
	}

	// Get disk usage
	if diskUsage, err := sc.getDiskUsage(); err == nil {
		info.DiskUsage = diskUsage
	}

	// Get system uptime
	if uptime, err := host.Uptime(); err == nil {
		info.Uptime = int64(uptime)
	}

	sc.logger.Infof("Collected system info for host: %s", info.Hostname)
	return info, nil
}

// getDiskUsage calculates the overall disk usage percentage
func (sc *SystemCollector) getDiskUsage() (float64, error) {
	partitions, err := disk.Partitions(false)
	if err != nil {
		return 0, err
	}

	var totalUsed, totalSize uint64
	for _, partition := range partitions {
		// Skip system partitions and removable drives
		if sc.shouldSkipPartition(partition) {
			continue
		}

		if usage, err := disk.Usage(partition.Mountpoint); err == nil {
			totalUsed += usage.Used
			totalSize += usage.Total
		}
	}

	if totalSize == 0 {
		return 0, fmt.Errorf("no valid partitions found")
	}

	return float64(totalUsed) / float64(totalSize) * 100, nil
}

// shouldSkipPartition determines if a partition should be skipped
func (sc *SystemCollector) shouldSkipPartition(partition disk.PartitionStat) bool {
	// Skip system partitions
	systemPaths := []string{
		"\\System Volume Information",
		"\\Recovery",
		"\\$Recycle.Bin",
	}

	for _, path := range systemPaths {
		if strings.Contains(partition.Mountpoint, path) {
			return true
		}
	}

	// Skip removable drives
	if strings.Contains(partition.Device, "\\\\.\\") {
		return true
	}

	return false
}

// GetSystemHealth calculates overall system health score
func (sc *SystemCollector) GetSystemHealth() (float64, error) {
	info, err := sc.CollectSystemInfo()
	if err != nil {
		return 0, err
	}

	// Calculate health score based on various metrics
	var healthScore float64
	var totalMetrics int

	// Memory health (lower usage is better)
	if info.TotalMemory > 0 {
		memoryUsage := float64(info.TotalMemory-info.AvailableMemory) / float64(info.TotalMemory) * 100
		if memoryUsage < 70 {
			healthScore += 100
		} else if memoryUsage < 85 {
			healthScore += 70
		} else if memoryUsage < 95 {
			healthScore += 40
		} else {
			healthScore += 10
		}
		totalMetrics++
	}

	// CPU health (lower usage is better)
	if info.CPUUsage < 70 {
		healthScore += 100
	} else if info.CPUUsage < 85 {
		healthScore += 70
	} else if info.CPUUsage < 95 {
		healthScore += 40
	} else {
		healthScore += 10
	}
	totalMetrics++

	// Disk health (lower usage is better)
	if info.DiskUsage < 70 {
		healthScore += 100
	} else if info.DiskUsage < 85 {
		healthScore += 70
	} else if info.DiskUsage < 95 {
		healthScore += 40
	} else {
		healthScore += 10
	}
	totalMetrics++

	if totalMetrics == 0 {
		return 0, fmt.Errorf("no metrics available for health calculation")
	}

	return healthScore / float64(totalMetrics), nil
}

// CollectPerformanceMetrics collects real-time performance metrics
func (sc *SystemCollector) CollectPerformanceMetrics() (map[string]interface{}, error) {
	metrics := make(map[string]interface{})

	// CPU metrics
	if cpuPercent, err := cpu.Percent(1, false); err == nil && len(cpuPercent) > 0 {
		metrics["cpu_usage"] = cpuPercent[0]
	}

	// Memory metrics
	if memInfo, err := mem.VirtualMemory(); err == nil {
		metrics["memory_total"] = memInfo.Total
		metrics["memory_used"] = memInfo.Used
		metrics["memory_available"] = memInfo.Available
		metrics["memory_usage_percent"] = memInfo.UsedPercent
	}

	// Disk I/O metrics
	if diskIO, err := disk.IOCounters(); err == nil {
		for name, io := range diskIO {
			metrics[fmt.Sprintf("disk_%s_read_bytes", name)] = io.ReadBytes
			metrics[fmt.Sprintf("disk_%s_write_bytes", name)] = io.WriteBytes
			metrics[fmt.Sprintf("disk_%s_read_count", name)] = io.ReadCount
			metrics[fmt.Sprintf("disk_%s_write_count", name)] = io.WriteCount
		}
	}

	// Network metrics (basic)
	metrics["network_connections"] = 0 // Would need to implement network connection counting

	// Process count
	if processCount, err := sc.getProcessCount(); err == nil {
		metrics["process_count"] = processCount
	}

	metrics["timestamp"] = time.Now()

	return metrics, nil
}

// getProcessCount gets the current process count
func (sc *SystemCollector) getProcessCount() (int, error) {
	// This is a simplified version - would typically use gopsutil/process
	return 100, nil
}

// CollectDiskInfo collects detailed disk information
// func (sc *SystemCollector) CollectDiskInfo() ([]map[string]interface{}, error) {
// 	var diskInfos []map[string]interface{}

// 	partitions, err := disk.Partitions(false)
// 	if err != nil {
// 		return nil, err
// 	}

// 	for _, partition := range partitions {
// 		if sc.shouldSkipPartition(partition) {
// 			continue
// 		}

// 		usage, err := disk.Usage(partition.Mountpoint)
// 		if err != nil {
// 			continue
// 		}

// 		diskInfo := map[string]interface{}{
// 			"device":              partition.Device,
// 			"mountpoint":          partition.Mountpoint,
// 			"fstype":              partition.Fstype,
// 			"total":               usage.Total,
// 			"used":                usage.Used,
// 			"free":                usage.Free,
// 			"usage_percent":       usage.UsedPercent,
// 			"inodes_total":        usage.InodesTotal,
// 			"inodes_used":         usage.InodesUsed,
// 			"inodes_free":         usage.InodesFree,
// 			"inodes_used_percent": usage.InodesUsedPercent,
// 		}

// 		diskInfos = append(diskInfos, diskInfo)
// 	}

// 	return diskInfos, nil
// }

// CollectNetworkInterfaces collects network interface information
// func (sc *SystemCollector) CollectNetworkInterfaces() ([]map[string]interface{}, error) {
// 	// This would typically use gopsutil/net package
// 	// For now, return basic interface info
// 	interfaces := []map[string]interface{}{
// 		{
// 			"name":        "Ethernet",
// 			"type":        "wired",
// 			"status":      "up",
// 			"speed":       1000,
// 			"mac_address": "00:00:00:00:00:00",
// 		},
// 		{
// 			"name":        "Wi-Fi",
// 			"type":        "wireless",
// 			"status":      "up",
// 			"speed":       300,
// 			"mac_address": "00:00:00:00:00:01",
// 		},
// 	}

// 	return interfaces, nil
// }

// CollectInstalledSoftware collects information about installed software
// func (sc *SystemCollector) CollectInstalledSoftware() ([]map[string]interface{}, error) {
// 	// This would typically query the Windows Registry
// 	// For now, return basic software info
// 	software := []map[string]interface{}{
// 		{
// 			"name":         "Windows Security Agent",
// 			"version":      "1.0.0",
// 			"publisher":    "Security Team",
// 			"install_date": time.Now().AddDate(0, 0, -30),
// 		},
// 	}

// 	return software, nil
// }

// CollectSystemEvents collects system events from Windows Event Log
// func (sc *SystemCollector) CollectSystemEvents() ([]map[string]interface{}, error) {
// 	// This would typically query the Windows Event Log
// 	// For now, return basic system events
// 	events := []map[string]interface{}{
// 		{
// 			"source":    "System",
// 			"event_id":  1001,
// 			"level":     "Information",
// 			"message":   "System started successfully",
// 			"timestamp": time.Now(),
// 		},
// 	}

// 	return events, nil
// }
