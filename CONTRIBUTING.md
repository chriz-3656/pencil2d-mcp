# Contributing to pencil2d-mcp

Thank you for your interest in improving `pencil2d-mcp`! We welcome contributions, bug reports, feature suggestions, and documentation improvements.

---

## Code of Conduct

This project is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

---

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/chriz-3656/pencil2d-mcp.git
   cd pencil2d-mcp
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   pip install -e .
   ```

4. **Run the test suite:**
   ```bash
   python -m unittest discover tests
   ```

---

## Submitting Pull Requests

1. Fork the repo and create your feature branch: `git checkout -b feature/awesome-feature`
2. Ensure existing and new tests pass.
3. Keep code clean and well-documented.
4. Commit your changes: `git commit -m 'Add awesome feature'`
5. Push to the branch: `git push origin feature/awesome-feature`
6. Open a Pull Request on GitHub targeting `main`.

---

## Questions and Support

Feel free to open an issue or reach out to the maintainer: **@chriz-3656**.
