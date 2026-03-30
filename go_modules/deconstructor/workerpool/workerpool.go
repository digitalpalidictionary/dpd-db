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
