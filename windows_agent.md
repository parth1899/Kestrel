# Windows Agent - Deep Architecture Analysis

## Overview

The windows-agent is a sophisticated real-time endpoint security monitoring system built in Go. It implements a **multi-layered concurrent architecture** that efficiently collects, processes, and distributes telemetry data from Windows systems. The design prioritizes **low latency**, **high throughput**, and **graceful shutdown** under load. // euu

---

## Core Architecture Philosophy

### Design Principles

1. **Separation of Concerns**: The system is divided into distinct layers:
   - **Collectors** (data acquisition layer)
   - **TelemetryService** (orchestration layer)
   - **Repository** (persistence layer)
   - **RabbitMQ** (messaging/distribution layer)

2. **Asynchronous Processing**: Everything operates asynchronously to prevent blocking operations from affecting real-time monitoring capabilities.

3. **Backpressure Handling**: The system gracefully handles overload situations by dropping events rather than crashing or blocking.

4. **Graceful Shutdown**: All components can be cleanly stopped without data loss or corruption.

---

## Concurrency Model Deep Dive

### 1. The Producer-Consumer Pattern with Channels

The agent uses Go's channel-based communication to implement a **loosely coupled producer-consumer architecture**. This is critical for several reasons:

**Why Channels?**
- **Decoupling**: Collectors don't need to know about storage or messaging implementations
- **Buffering**: Channels provide natural backpressure - when full, producers are blocked (or can drop)
- **Type Safety**: Channels are strongly typed, preventing runtime errors
- **Goroutine Coordination**: Channels are the idiomatic way to coordinate goroutines in Go
(idiomatic matlab natural or conventional way ;)

**Channel Sizing Strategy** (see `process_collector.go:32`)
- Each collector uses a **buffered channel with capacity 1000**
- This size is a balance between:
  - **Memory usage**: 1000 events × average event size
  - **Burst tolerance**: Can handle sudden spikes in events
  - **Latency**: If channel is full, events are dropped (see non-blocking sends below)

**Why 1000?**
- Typical event rate: ~10-100 events/second per collector
- 1000 events = 10-100 seconds of buffer at normal load
- Prevents blocking during brief database write delays
- Small enough to fail fast if there's a serious problem

### 2. Non-Blocking Event Sending

The collectors use a critical pattern for handling channel overflow (see `process_collector.go:122-127`):

```go
select {
case pc.processChan <- *processEvent:
    // Successfully sent
default:
    // Channel full - drop event
}
```

**Why Non-Blocking?**
- **Prevents Deadlock**: If the consumer (event loop) is blocked on database write, the producer (collector) won't block forever
- **Graceful Degradation**: Under extreme load, the system continues monitoring but drops some events rather than crashing
- **Real-time Guarantee**: Critical monitoring continues even if storage is slow

**Trade-off**: Some events may be lost under extreme load, but this is preferable to system failure in a security monitoring context.

### 3. Context-Based Cancellation

The entire system uses `context.Context` for coordinated shutdown (see `telemetry_service.go:51`):
(context basically tells multiple goroutines to do a work, without it all would run till they end naturally)
**How It Works:**
1. `TelemetryService` creates a cancellable context at initialization
2. All goroutines receive this context
3. When `Stop()` is called, `ts.cancel()` is invoked (line 253)
4. All goroutines check `ctx.Done()` in their select statements
5. When context is cancelled, all goroutines exit cleanly

**Why Context?**
- **Propagation**: Cancellation signal automatically propagates to all child goroutines
- **Timeout Support**: Can add timeouts easily (e.g., `context.WithTimeout`)
- **Standard Pattern**: Idiomatic Go for cancellation
- **Composability**: Can combine multiple contexts (deadline + cancellation)

**Example Flow** (see `process_collector.go:61-69`):
- The monitoring loop runs in a goroutine
- It checks `ctx.Done()` in every iteration
- When cancelled, it stops the ticker, closes the channel, and returns
- This ensures no goroutine leaks

### 4. Mutex Protection Strategy

The collectors maintain internal state that must be thread-safe:

**Process Collector State** (see `process_collector.go:23-24`):
- `knownProcesses map[int32]bool` - tracks which processes we've seen
- `knownMutex sync.RWMutex` - protects the map

**Why RWMutex?**
- **Read-Heavy Workload**: Most operations are reads (checking if process exists)
- **Performance**: Multiple readers can proceed concurrently
- **Write Safety**: Only one writer at a time (when updating the map)

**Locking Pattern** (see `process_collector.go:87-88`):
```go
pc.knownMutex.Lock()
defer pc.knownMutex.Unlock()
```

**Critical Section Analysis:**
- The lock is held during the entire `detectProcessChanges()` operation
- This is safe because:
  - The operation is fast (just map lookups and updates)
  - It happens once per second (not high-frequency)
  - The lock scope is minimal (only the state update, not event creation)



### 5. WaitGroup for Graceful Shutdown

The `TelemetryService` uses `sync.WaitGroup` to coordinate shutdown (see `telemetry_service.go:39, 95, 108`):

**How It Works:**
1. Before starting goroutines: `ts.wg.Add(4)` - expect 4 goroutines
2. Each event loop: `defer ts.wg.Done()` - signals completion
3. During shutdown: `ts.wg.Wait()` - blocks until all complete (blocks main(it is also a goroutine))

**Why WaitGroup?**
- **Coordination**: Ensures all goroutines finish before shutdown completes
- **No Manual Tracking**: Don't need to track goroutine IDs or channels
- **Timeout Protection**: Combined with `select` and timeout (line 265-270) prevents indefinite blocking

**Shutdown Sequence** (see `telemetry_service.go:241-283`):
1. Lock mutex (prevent concurrent Start/Stop)
2. Cancel context (signal all goroutines to stop)
3. Set `running = false`
4. Wait for all goroutines with 10-second timeout
5. Close channels and connections
6. Unlock mutex

**Why 10-Second Timeout?**
- Prevents hanging if a goroutine is stuck
- Long enough for normal cleanup (database writes, channel drains)
- Short enough to fail fast if something is wrong

---

## Event Collection Mechanisms

### 1. Process Monitoring - Polling with State Tracking

**Architecture** (see `process_collector.go:38-71`):
- Uses **differential polling** - compares current state to previous state
- Polls every **1 second** using `time.Ticker`
- Maintains `knownProcesses` map to track seen processes

**Why Polling Instead of Events?**
- **Cross-Platform**: Windows doesn't have reliable process creation events without ETW (Event Tracing for Windows)
- **Simplicity**: Polling is straightforward and works everywhere
- **Reliability**: No event loss from missed notifications
- **Trade-off**: 1-second latency vs. real-time (acceptable for security monitoring)

**State Tracking Algorithm**:
1. Get current process list
2. Compare to `knownProcesses` map
3. **New processes**: Not in map → create "start" event
4. **Terminated processes**: In map but not current → create "stop" event
5. Update map with current state

**Memory Efficiency**:
- Only stores PID (int32) and boolean - minimal memory
- Map automatically grows/shrinks with process count
- Typical system: 50-200 processes = ~1-4KB memory



### 2. File Monitoring - Event-Driven with fsnotify

**Architecture** (see `file_collector.go:32-99`):
- Uses **fsnotify** library for OS-level file system events
- Watches specific directories (TEMP, Downloads, Desktop, Documents)
- Handles CREATE, WRITE, REMOVE, RENAME events

**Why Event-Driven?**
- **Real-time**: Events fire immediately when files change
- **Efficient**: Only processes actual changes, not full directory scans
- **Low Overhead**: OS kernel handles the heavy lifting

**Why Not Watch Everything?**
- **Performance**: Watching entire filesystem would be too expensive
- **Noise**: Most files are irrelevant (system files, caches)
- **Focus**: Security-relevant files are typically in user directories

**Debouncing Strategy** (see `file_collector.go:108-111`):
- Maintains `recentFiles` map with timestamps
- Skips files seen within last 5 minutes
- Prevents duplicate events from rapid file modifications

**Why Debouncing?**
- **File Operations**: Many programs create temp files, modify, delete rapidly
- **Event Storms**: A single save can trigger multiple WRITE events
- **Storage Efficiency**: Reduces database writes by 80-90%

**Cleanup Mechanism** (see `telemetry_service.go:142-154`):
- Separate goroutine runs every 5 minutes
- Removes entries older than 10 minutes from `recentFiles`
- Prevents memory leak from map growth

### 3. Network Monitoring - Polling with Connection Diffing

**Architecture** (see `network_collector.go:48-87`):
- Polls every **2 seconds** using `time.Ticker`
- Maintains `previousConns` map to track known connections
- Detects new connections by comparing current vs. previous state

**Why 2-Second Polling?**
- **Balance**: More frequent than process (1s) because network changes faster
- **Overhead**: Network connection enumeration is expensive (~50-200ms)
- **Trade-off**: 2 seconds provides good balance between latency and CPU usage

**State Diffing Algorithm**:
1. Get current connections from `net.Connections("all")`
2. Create map keyed by connection signature (IP:Port pairs + PID)
3. Compare to `previousConns` map
4. **New connections**: Not in previous → create event
5. Update `previousConns` with current state

**Connection Key Generation** (see `network_collector.go:211-216`):
- Format: `"localIP:localPort-remoteIP:remotePort-protocol-PID"`
- Uniquely identifies a connection
- Includes PID to track which process owns the connection

**Why Track Previous State?**
- **Event Reduction**: Only report new connections, not all connections every poll
- **Efficiency**: Reduces events by 95%+ (most connections are long-lived)
- **Relevance**: Security monitoring cares about new connections, not existing ones

**Memory Management**:
- `previousConns` map grows with active connections
- Typical system: 20-100 active connections = ~5-25KB
- `recentConnections` map for deduplication (cleaned every 2 minutes)

### 4. System Monitoring - Periodic Sampling

**Architecture** (see `telemetry_service.go:214-239`):
- Runs every **5 minutes** using `time.Ticker`
- Collects comprehensive system metrics (CPU, memory, disk, uptime)
- Single-shot collection (not event-driven)

**Why 5 Minutes?**
- **System Metrics Change Slowly**: CPU/memory/disk don't change second-to-second
- **Storage Efficiency**: System info is large (many fields), frequent writes would be wasteful
- **Query Performance**: 5-minute intervals provide good historical data without bloat

**What Gets Collected** (see `system_collector.go:37-83`):
- Hostname, OS version, architecture
- Total/available memory
- CPU count and usage percentage
- Disk usage percentage
- System uptime

**Why Not Real-time?**
- **Cost-Benefit**: System health doesn't need second-level granularity
- **Resource Usage**: System info collection involves multiple syscalls
- **Use Case**: Used for trend analysis, not real-time alerting

---

## Data Flow and Processing Pipeline

### Event Lifecycle

1. **Collection Phase** (Collectors):
   - Process: Polls every 1s, detects changes
   - File: Receives OS events via fsnotify
   - Network: Polls every 2s, detects new connections
   - System: Samples every 5min

2. **Channel Transport**:
   - Events sent to buffered channels (capacity 1000)
   - Non-blocking sends (drops if full)
   - Type-safe communication

3. **Consumption Phase** (Event Loops):
   - Each collector has dedicated event loop goroutine
   - Loops read from channel using `range` (blocks until channel closed)
   - Processes each event sequentially

4. **Dual Write Pattern**:
   - **PostgreSQL**: Persistent storage for querying/analysis
   - **RabbitMQ**: Real-time distribution to other systems
   - Both writes happen in same loop iteration
   - If one fails, other still succeeds (independent operations)

### Why Separate Event Loops?

Each collector has its own event loop goroutine (see `telemetry_service.go:97-100`):

**Benefits:**
- **Isolation**: Slow database write for process events doesn't block file events
- **Parallelism**: All collectors process events concurrently
- **Fault Tolerance**: Failure in one loop doesn't affect others
- **Resource Management**: Each loop can have different priorities/backoff strategies

Collector (goroutine 1)
    ↓ [ASYNC send - non-blocking if buffer has space]
Buffered Channel (1000 capacity)
    ↓ [SYNC receive - blocks until event available]
Event Loop (goroutine 2)
    ↓ [SYNC write - blocks until DB confirms]
PostgreSQL Database

### Database Write Strategy

**Synchronous Writes** (see `telemetry_service.go:122-125`):
- Each event is written immediately when received
- No batching or buffering
- Simple error handling

**Why Synchronous?**
- **Durability**: Events are persisted before acknowledging
- **Simplicity**: No need for complex batching logic
- **Low Latency**: Events appear in database immediately
- **Trade-off**: Slower than batching, but acceptable for security monitoring

**Error Handling**:
- Logs error but continues processing (see line 123)
- Prevents one bad event from stopping entire collector
- Errors are non-fatal - system continues monitoring

### RabbitMQ Publishing Strategy

Parth yeh part add karde if required

---

## Concurrency Safety and Race Conditions

### Shared State Protection

**TelemetryService State** (see `telemetry_service.go:28-46`):
- `running bool` - protected by `mutex sync.RWMutex`
- `ctx context.Context` - immutable after creation
- `cancel context.CancelFunc` - called once during shutdown

**Why RWMutex for `running`?**
- **Read-Heavy**: `IsRunning()` called frequently (line 286-289)
- **Write-Rare**: Only written during Start/Stop
- **Performance**: Multiple concurrent reads don't block

**Collector State**:
- Each collector maintains its own state
- No shared state between collectors
- Eliminates cross-collector race conditions

### Channel Safety

**Channel Ownership**:
- **Producer Owns**: Collector creates and closes channel
- **Consumer Uses**: Event loop reads until channel closed
- **No Concurrent Writes**: Only collector writes to channel
- **No Concurrent Reads**: Only event loop reads from channel

**Why This Matters:**
- Go channels are safe for concurrent use, but ownership pattern prevents confusion
- Closing channel signals "no more events" to consumer
- Consumer's `range` loop automatically exits when channel closed

### Context Cancellation Safety

**Cancellation Propagation**:
- Context created once in `NewTelemetryService` (line 51)
- Passed to all collectors and goroutines
- Cancelled once in `Stop()` (line 253)
- All goroutines check `ctx.Done()` in select statements

**Why Safe?**
- Context cancellation is thread-safe
- Multiple goroutines can check `ctx.Done()` concurrently
- No race conditions - context is read-only after creation

---





### Failure Modes and Recovery

**Collector Failure:**
- If collector crashes, its goroutine exits
- Other collectors continue operating
- No automatic restart (would require supervisor pattern)

**Database Failure:**
- Writes fail, errors logged
- Events continue to be collected (in channels)
- RabbitMQ publishing continues (independent)
- **Risk**: Channel fills up, events dropped
- **Recovery**: Database reconnection would require restart

**RabbitMQ Failure:**
- Publishing fails, errors logged
- Database writes continue
- Events still collected and stored
- **Impact**: Real-time distribution stops, but storage continues

**Channel Overflow:**
- If channel full and non-blocking send fails, event dropped
- Logged as warning
- Monitoring continues
- **Mitigation**: Increase channel size or improve consumer speed

---

## Design Trade-offs and Decisions

### Why Polling vs. Event-Driven?

**Process & Network: Polling**
- **Pros**: Simple, reliable, cross-platform
- **Cons**: Latency (1-2 seconds), CPU usage
- **Decision**: Acceptable trade-off for security monitoring

**File: Event-Driven**
- **Pros**: Real-time, efficient, low overhead
- **Cons**: Platform-specific (fsnotify), directory limits
- **Decision**: Best of both worlds - real-time where possible


### Why Synchronous Writes vs. Batching?

**Current: Synchronous**
- **Pros**: Simple, immediate persistence, no data loss risk
- **Cons**: Slower, more database connections
- **Decision**: Durability and simplicity over performance

**Alternative: Batching**
- Could batch 100 events, write every second
- **Pros**: Higher throughput, fewer connections
- **Cons**: Risk of data loss on crash, more complex
- **Not Chosen**: Security monitoring requires durability


## Advanced Concurrency Patterns

### 1. Fan-Out Pattern

Each event loop performs **fan-out** - one event goes to multiple destinations:
- Database write
- RabbitMQ publish

**Implementation** (see `telemetry_service.go:121-129`):
- Sequential writes (database, then RabbitMQ)
- Independent error handling
- If one fails, other still executes

**Why Sequential?**
- Simpler than parallel (no need for sync)
- Database write is typically faster
- RabbitMQ failure doesn't block database

### 2. Worker Pool Pattern (Implicit)

The 4 event loops form an implicit worker pool:
- Each loop is a "worker"
- Channels are the "job queue"
- Collectors are the "job producers"

**Why Not Explicit Pool?**
- Each collector has different characteristics
- Different processing needs (file vs. system)
- Explicit pool would add complexity without benefit

### 3. Producer Rate Limiting

Collectors naturally rate-limit themselves:
- Process: 1 poll per second
- Network: 1 poll per 2 seconds
- File: OS event rate (unlimited, but debounced)
- System: 1 sample per 5 minutes

**Why No Explicit Rate Limiting?**
- Tickers provide natural rate limiting
- Debouncing handles file event storms
- Simpler than token bucket or leaky bucket

### 4. Graceful Degradation

The system gracefully degrades under load:
- Channel overflow: Events dropped (non-blocking sends)
- Database slow: Events queued in channel
- RabbitMQ down: Database writes continue
- Collector crash: Other collectors unaffected

**Philosophy**: Better to lose some events than crash entire system

---

## Summary

The windows-agent demonstrates sophisticated use of Go's concurrency primitives:

1. **Channels** for type-safe, buffered communication
2. **Goroutines** for parallel processing
3. **Context** for coordinated cancellation
4. **Mutexes** for shared state protection
5. **WaitGroups** for graceful shutdown

