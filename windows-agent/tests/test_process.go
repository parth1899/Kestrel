package main

import (
	"context"
	"fmt"
	"time"

	"windows-agent/collectors"

	"github.com/sirupsen/logrus"
)

func main() {
	logger := logrus.New()
	logger.SetLevel(logrus.DebugLevel)

	collector := collectors.NewProcessCollector("test-agent", logger)

	// Start real-time monitoring
	ctx := context.Background()
	collector.StartRealTimeMonitoring(ctx)

	// Listen for events
	go func() {
		for event := range collector.GetProcessChannel() {
			fmt.Printf("Process Event: %s (PID: %d) - %s\n",
				event.ProcessName, event.ProcessID, event.EventType)
		}
	}()

	// Run for 30 seconds
	time.Sleep(30 * time.Second)
	fmt.Println("Test completed")
}
