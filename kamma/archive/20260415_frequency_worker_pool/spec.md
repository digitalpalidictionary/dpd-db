# Spec: Frequency Worker Pool

## Overview
Replace unbounded goroutine spawning (~60k+ goroutines) in `go_modules/frequency/main.go` with the existing `workerpool.Run` pattern from `go_modules/deconstructor/workerpool`.

## What it should do
- Use a fixed pool of `runtime.NumCPU()*2` workers consuming from a buffered channel
- Reuse the generic `workerpool.Run[T]` from `dpd/go_modules/deconstructor/workerpool`
- Each worker processes one headword at a time
- Results still collected in `htmlStash`/`dataStash` with mutex (contention drops from 60k goroutines to ~N workers)
- Output is byte-identical

## Assumptions
- The database has ~60k+ headwords (minus idioms)
- The work per headword is CPU-bound (map lookups, template rendering)
- `runtime.NumCPU()*2` is a good default, matching the deconstructor pattern

## Constraints
- Don't change freqFinder, gradient, template, or updateDb logic
- Don't change the output format
- Keep counter/progress printing working

## How we'll know it's done
- CPU usage drops significantly (no longer 100% on all cores from scheduler thrashing)
- Runtime is the same or better
- Output is identical

## What's not included
- Optimizing freqFinder's nested loop algorithm
- Changing the database update strategy
- Adding CLI flags for worker count
