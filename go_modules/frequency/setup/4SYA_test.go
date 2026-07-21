package main

import (
	"reflect"
	"strings"
	"testing"
)

// A normal SYA file is returned as a single slice keyed by its own path,
// with its text untouched.
func TestSyaFileSlicesPassthrough(t *testing.T) {
	text := "namo tassa bhagavato\npage number: 001\nsome pāḷi words"
	got := syaFileSlices("Canonical/09-Digha-1.txt", text)

	want := map[string]string{"Canonical/09-Digha-1.txt": text}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("passthrough = %v, want %v", got, want)
	}
}

// The combined volume 26 is split at the Theragāthā heading: that line and
// everything after it goes to the th-thi slice, everything before to vv-pv.
func TestSyaFileSlicesSplit26(t *testing.T) {
	vvPv := "suttantapiṭake khuddakanikāyassa\nvimānavatthu\n[1] pīṭhante sovaṇṇamayaṁ\n"
	thThi := syaTheraMarker + "\n[137] sīhānaṁva nadantānaṁ\ntheragāthāya paṭhamo\n"
	text := vvPv + thThi

	got := syaFileSlices(syaCombinedVol, text)

	if len(got) != 2 {
		t.Fatalf("expected 2 slices, got %d: %v", len(got), got)
	}
	if got[syaVvPvKey] != vvPv {
		t.Errorf("vv-pv slice = %q, want %q", got[syaVvPvKey], vvPv)
	}
	if got[syaThThiKey] != thThi {
		t.Errorf("th-thi slice = %q, want %q", got[syaThThiKey], thThi)
	}

	// Conservation: the two slices must recombine to the exact original text,
	// so no token is dropped or double-counted at the seam.
	if got[syaVvPvKey]+got[syaThThiKey] != text {
		t.Errorf("slices do not recombine to the original text")
	}

	// The marker line itself belongs to the th-thi (Khuddaka 1) side.
	if !strings.HasPrefix(got[syaThThiKey], syaTheraMarker) {
		t.Errorf("th-thi slice must start with the Theragāthā marker")
	}
	if strings.Contains(got[syaVvPvKey], syaTheraMarker) {
		t.Errorf("vv-pv slice must not contain the Theragāthā marker")
	}
}

// A missing marker in the combined volume is a hard error, not a silent
// mis-slice, so a corpus change that moves the heading fails loudly.
func TestSyaFileSlicesMissingMarkerPanics(t *testing.T) {
	defer func() {
		if recover() == nil {
			t.Errorf("expected panic when the Theragāthā marker is absent")
		}
	}()
	syaFileSlices(syaCombinedVol, "vimānavatthu with no thera heading")
}
