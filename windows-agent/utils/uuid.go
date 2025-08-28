package utils

import (
	"crypto/rand"
	"fmt"
	"time"
)

// GenerateUUID generates a simple UUID-like string
func GenerateUUID() string {
	b := make([]byte, 16)
	_, err := rand.Read(b)
	if err != nil {
		// Fallback to timestamp-based ID if random generation fails
		return fmt.Sprintf("id-%d-%d", time.Now().UnixNano(), time.Now().Unix())
	}
	return fmt.Sprintf("%x-%x-%x-%x-%x", b[0:4], b[4:6], b[6:8], b[8:10], b[10:])
}

// GenerateShortID generates a shorter ID for internal use
func GenerateShortID() string {
	b := make([]byte, 8)
	_, err := rand.Read(b)
	if err != nil {
		return fmt.Sprintf("id-%d", time.Now().UnixNano())
	}
	return fmt.Sprintf("%x", b)
}

// GenerateTimestampID generates an ID based on timestamp
func GenerateTimestampID() string {
	return fmt.Sprintf("ts-%d", time.Now().UnixNano())
}

// IsValidUUID checks if a string is a valid UUID format
func IsValidUUID(uuid string) bool {
	if len(uuid) != 36 {
		return false
	}
	
	// Check format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
	for i, char := range uuid {
		if i == 8 || i == 13 || i == 18 || i == 23 {
			if char != '-' {
				return false
			}
		} else {
			if !((char >= '0' && char <= '9') || (char >= 'a' && char <= 'f') || (char >= 'A' && char <= 'F')) {
				return false
			}
		}
	}
	return true
}
