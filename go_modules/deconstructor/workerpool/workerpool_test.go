package workerpool_test

import (
	"dpd/go_modules/deconstructor/workerpool"
	"runtime"
	"sync/atomic"
	"testing"
	"time"
)

func makeJobs(n int) <-chan int {
	ch := make(chan int, n)
	for i := range n {
		ch <- i
	}
	close(ch)
	return ch
}

// All items sent through the channel must be processed exactly once.
func TestRun_ProcessesAllItems(t *testing.T) {
	const itemCount = 200
	var processedCount int64

	workerpool.Run(runtime.NumCPU(), makeJobs(itemCount), func(_ int) {
		atomic.AddInt64(&processedCount, 1)
	})

	if processedCount != itemCount {
		t.Errorf("expected %d items processed, got %d", itemCount, processedCount)
	}
}

// Run must return (all workers terminate) after the jobs channel closes.
func TestRun_WorkersTerminateOnChannelClose(t *testing.T) {
	done := make(chan struct{})
	go func() {
		workerpool.Run(runtime.NumCPU(), makeJobs(50), func(_ int) {})
		close(done)
	}()

	select {
	case <-done:
	case <-time.After(5 * time.Second):
		t.Error("worker pool did not terminate within 5s after channel closed")
	}
}

// Concurrent workers must not exceed numWorkers at any point.
func TestRun_BoundedConcurrency(t *testing.T) {
	numWorkers := runtime.NumCPU()
	const itemCount = 500

	var current, peak int64

	workerpool.Run(numWorkers, makeJobs(itemCount), func(_ int) {
		c := atomic.AddInt64(&current, 1)
		for {
			p := atomic.LoadInt64(&peak)
			if c <= p || atomic.CompareAndSwapInt64(&peak, p, c) {
				break
			}
		}
		atomic.AddInt64(&current, -1)
	})

	if peak > int64(numWorkers) {
		t.Errorf("peak concurrency %d exceeded numWorkers %d", peak, numWorkers)
	}
}
