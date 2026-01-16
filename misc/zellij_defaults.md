# Zellij Defaults (Optimized for Locked Mode)

Your configuration uses the `shared_among "normal" "locked"` block, which means the following **Alt shortcuts work immediately**, even while in **Locked Mode**.

## 1. Instant Navigation (Works in Locked Mode)
| Shortcut | Action |
| --- | --- |
| **`Alt + h`** / **`Left`** | Switch focus **Left** (Tab or Pane) |
| **`Alt + l`** / **`Right`** | Switch focus **Right** (Tab or Pane) |
| **`Alt + j`** / **`Down`** | Switch focus **Down** |
| **`Alt + k`** / **`Up`** | Switch focus **Up** |
| **`Alt + i`** | Move current Tab position **Left** |
| **`Alt + o`** | Move current Tab position **Right** |

---

## 2. Quick Layouts & Panes (Works in Locked Mode)
| Shortcut | Action |
| --- | --- |
| **`Alt + [`** | Previous Swap Layout |
| **`Alt + ]`** | Next Swap Layout |
| **`Alt + n`** | Create New Pane |
| **`Alt + f`** | Toggle Floating Panes |
| **`Alt + p`** | Toggle Pane in Group |
| **`Alt + =`** / **`+`** | Increase Pane Size |
| **`Alt + -`** | Decrease Pane Size |

---

## 3. Operations requiring Normal Mode (`Ctrl + g` first)
To access these specialized menus, you must first unlock with **`Ctrl + g`**:

| Shortcut | Mode | Keys inside mode |
| --- | --- | --- |
| **`t`** | **Tab Mode** | `1-9` (Jump), `x` (Close), `r` (Rename), `tab` (Toggle) |
| **`p`** | **Pane Mode** | `f` (Fullscreen), `z` (Frames), `d/r/s` (Split Down/Right/Stacked) |
| **`s`** | **Scroll Mode** | `f` (Search), `e` (Edit Scrollback), `j/k` (Scroll) |
| **`m`** | **Move Mode** | `h/j/k/l` (Rearrange panes) |
| **`r`** | **Resize Mode** | `h/j/k/l` (Directional resize) |
| **`o`** | **Session Mode** | `d` (Detach), `w` (Manager) |

---

## Workflow Summary
- **Switching Tabs/Panes:** Just use `Alt + h/l/j/k`.
- **Moving Tabs:** Just use `Alt + i/o`.
- **Close/Rename/Specific Jump:** `Ctrl + g` → `t` (Tab) or `p` (Pane) → Action.
- **Relocking:** Your config automatically returns to **Locked Mode** after most actions (e.g., creating a new pane or closing one).