# Plan: Frequency Worker Pool

## Phase 1: Worker Pool

- [x] Import `dpd/go_modules/deconstructor/workerpool` and `runtime` in main.go
- [x] Replace the goroutine-per-word loop in main() with channel + workerpool.Run pattern
- [x] Remove global `wg sync.WaitGroup` and wg.Add/wg.Done calls from makeFreqTable
- [x] Keep the mutex for htmlStash/dataStash (now only N workers contending, not 60k)
  -> verify: `go build ./go_modules/frequency/` compiles; `go vet ./go_modules/frequency/...` passes ✓
- [x] Add `just freq` recipe to justfile
