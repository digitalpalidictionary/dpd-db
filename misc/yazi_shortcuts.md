# Yazi Shortcuts and Hotkeys for Linux

Yazi is a blazing-fast terminal file manager written in Rust. Below is a comprehensive guide to its default keyboard shortcuts.

## Navigation

| Key | Action |
| --- | --- |
| `j` / `↓` | Move cursor down |
| `k` / `↑` | Move cursor up |
| `h` / `←` | Go to parent directory |
| `l` / `→` | Enter hovered directory |
| `g` + `g` | Move cursor to the top |
| `G` | Move cursor to the bottom |
| `z` | Change directory or reveal file using `fzf` |
| `Z` | Change directory using `zoxide` |
| `g` + `Space` | Change directory or reveal file via interactive prompt |
| `Ctrl` + `u` | Move up half page |
| `Ctrl` + `d` | Move down half page |
| `Ctrl` + `b` | Move up full page |
| `Ctrl` + `f` | Move down full page |

## Selection

| Key | Action |
| --- | --- |
| `Space` | Toggle selection of hovered file |
| `v` | Enter visual mode (selection mode) |
| `V` | Enter visual mode (unset mode) |
| `Ctrl` + `a` | Select all files |
| `Ctrl` + `r` | Inverse selection of all files |
| `Esc` / `Ctrl` + `[` | Cancel selection |

## File Operations

| Key | Action |
| --- | --- |
| `Enter` / `o` | Open selected file(s) |
| `a` | Create file or directory (append `/` for directory) |
| `r` | Rename selected file(s) |
| `y` | Copy (yank) selected file(s) |
| `x` | Cut selected file(s) |
| `p` | Paste file(s) |
| `P` | Paste and overwrite if destination exists |
| `d` | Delete (move to trash) |
| `D` | Permanently delete |
| `;` | Run shell command (background) |
| `:` | Run shell command (blocking) |

## Copy Path Components

| Key | Action |
| --- | --- |
| `c` + `c` | Copy file path |
| `c` + `d` | Copy directory path |
| `c` + `f` | Copy filename |
| `c` + `n` | Copy filename without extension |

## Tabs

| Key | Action |
| --- | --- |
| `t` | Create a new tab |
| `1`-`9` | Switch to tab N |
| `[` | Switch to previous tab |
| `]` | Switch to next tab |
| `w` | Close current tab |

## Filtering & Searching

| Key | Action |
| --- | --- |
| `f` | Filter files incrementally |
| `/` | Search files using `ripgrep` |
| `n` | Go to next search match |
| `N` | Go to previous search match |

## Miscellaneous

| Key | Action |
| --- | --- |
| `.` | Toggle hidden files |
| `q` | Quit Yazi |
| `F1` / `~` | Open help menu |
| `m` | Manage tasks |
| `w` | Open the tasks manager |

---
*Note: Keybindings can be customized in the `keymap.toml` configuration file.*
