package workerpool

import "sync"

// Run starts numWorkers goroutines that consume jobs from the channel,
// calling fn for each job. Returns when the channel is closed and all
// workers have finished.
func Run[T any](numWorkers int, jobs <-chan T, fn func(T)) {
	var wg sync.WaitGroup
	for range numWorkers {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for job := range jobs {
				fn(job)
			}
		}()
	}
	wg.Wait()
}

// RunCollect starts numWorkers goroutines, each owning its own state built by
// newState. Each job is handled by fn(state, job) using only that worker's
// state, so fn needs no locking. Returns the per-worker states for merging once
// all jobs are done.
func RunCollect[S any, T any](numWorkers int, newState func() S, jobs <-chan T, fn func(S, T)) []S {
	var wg sync.WaitGroup
	states := make([]S, numWorkers)
	for i := range numWorkers {
		states[i] = newState()
		wg.Add(1)
		go func(s S) {
			defer wg.Done()
			for job := range jobs {
				fn(s, job)
			}
		}(states[i])
	}
	wg.Wait()
	return states
}
