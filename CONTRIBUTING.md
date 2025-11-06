# Contributing

Thanks for wanting to contribute to Network Device Monitor. This document covers the common workflows for development, testing and submitting changes.

Getting started

1. Fork the repo and create a feature branch from `main`.

2. Create a local Python virtualenv and install backend dev deps:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements/dev.txt
```

3. Copy and edit environment template:

```bash
cp backend/.env.example backend/.env
# Edit backend/.env to set INFLUX_TOKEN, INFLUX_URL etc.
```

Development workflow

- Run the backend in dev mode:

```bash
make dev
```

- Run frontend locally (recommended while developing UI):

```bash
make run-frontend
```

Testing

- Run backend tests:

```bash
make -C backend test
```

- Run frontend PyQt tests (requires a display / pytest-qt):

```bash
cd frontend/pyqt && pytest -q
```

Linting and type checks

- Lint and format: `make -C backend lint`
- Typecheck: `make -C backend typecheck`

Commit and PR

- Keep changes small and focused.
- Write tests for new behavior where possible.
- Open a pull request to `main` and include a short description and testing notes.

Code of conduct

Be respectful and follow the project's issue/PR templates.
