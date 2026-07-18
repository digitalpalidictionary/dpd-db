# Plan: SC variants in freq maps

## Tasks

- [x] 1. Add `ScVariantTextDir` to `go_modules/tools/pth.go`
       → verify: `go vet ./go_modules/...` ✓
- [x] 2. Add `extractVariantWords()` + variant-file merge to
       `go_modules/frequency/setup/2SC.go`
       → verify: `go vet ./go_modules/...` ✓
- [x] 3. Add `go_modules/frequency/setup/2SC_test.go` unit tests
       → verify: `go test ./go_modules/frequency/setup/` — 6/6 pass
- [x] 4. Smoke: `go build ./go_modules/...` + full `go test ./go_modules/...` — all pass

## Status

Thread created 2026-07-18 after viability study (see spec.md).
Implementation complete 2026-07-18; gofmt/vet/build/tests all clean.

Review 2026-07-18 (parallel: kamma review agent + CodeRabbit):
- [x] CodeRabbit: `os.Stat` swallowed non-ENOENT errors → now `os.IsNotExist`
       check + `tools.HardCheck` for anything else
- [x] Kamma review: ~21 clauses with unclosed `(` leaked witness/citation junk
       into the freq map → clause now truncated at first unclosed `(`;
       spec.md investigation numbers corrected; 2 regression tests added
- [x] Re-verify: gofmt/vet clean, 8/8 unit tests pass

Awaiting user commit.
