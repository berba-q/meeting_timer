# Contributing to OnTime Meeting Timer

Thank you for your interest in contributing to bug fixes and new features! This guide outlines how to get started, the expected workflow, and our standards for commits and pull requests.

Special thanks to `Michael Mena`, `Antonio Montaperto` and `Clayton Smith` for their kind contributions to this project ⭐⭐⭐⭐⭐!

---

## 📦 Project Setup

To set up the project locally, see  [`DEVELOPER_GUIDE.md`](https://github.com/berba-q/meeting_timer/blob/v1.0.0/DEVELOPER_GUIDE.md). It includes details on environment setup, running the app, and testing.

---

## 🔄 Branching Strategy

- Use feature branches based on the latest release branch.
  - Example: `feature/splash-screen`, `fix/websocket-reconnect`
- Submit pull requests against the current dev branch (e.g. `v1.0.1`).
- Use meaningful branch names.

---

## ✅ Commit Messages

We use **Conventional Commits** to automatically generate changelogs and improve clarity.

### Common types:
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `chore`: Non-functional updates (build, tooling)
- `refactor`: Code improvements without feature or fix
- `test`: Adding or improving tests

### Example:
```bash
git commit -m "feat: add splash screen"