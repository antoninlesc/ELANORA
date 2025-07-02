# Contributing to the Elanora Project

Thank you for your interest in contributing to MDL-Corpus!  
This guide will help you get started and ensure a consistent workflow for all contributors.

---

## Branch Management

### Main Branches

- **`main`** – Production-ready code.
- **`dev`** – Main development branch.

### Supporting Branches

- **`feature/<name>`** – New features (e.g., `feature/user-authentication`).  
  When working on an issue, use `feature/issue-name`.
- **`test/<name>`** – Adding or updating tests.
- **`release/<version>`** – Release preparation (e.g., `release/1.3.5`).
- **`hotfix/<name>`** – Emergency fixes for production (e.g., `hotfix/security-patch`).
- **`docs/<name>`** – Documentation updates.

### Branch Flow

- Start new features from `dev` in a `feature/*` branch.
- Merge features into `dev` via Pull Requests (PRs).
- Create `release/*` branches from `dev` for releases.
- Merge `release/*` into both `main` and `dev` after testing.
- Create `hotfix/*` branches from `main` for urgent fixes, then merge back to both `main` and `dev`.

---

## Commit Message Guidelines

Follow the [Conventional Commits](https://www.conventionalcommits.org/) style:

```text
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

**Types:**

- `feat` – New feature
- `fix` – Bug fix
- `docs` – Documentation changes
- `style` – Code style changes (formatting, etc.)
- `refactor` – Code refactoring
- `test` – Adding or updating tests
- `chore` – Maintenance tasks
- `ci` – CI/CD related changes

**Scope:**  
Module or component name (e.g., `auth`, `api`, `ui`). Optional.

**Subject:**  

- Use imperative mood ("add" not "added" or "adds")
- No capitalization or period at the end
- Max 50 characters

**Examples:**

```text
feat(auth): add OAuth2 authentication
fix(api): handle null response from payment service
docs: update README with deployment instructions
test(user): add integration tests for user registration
ci(deploy): add staging environment deployment
```

**Best Practices:**

1. Keep commits atomic and focused.
2. Write meaningful commit messages.
3. Reference issue numbers in commit body or footer.
4. Separate subject from body with a blank line.
5. Wrap body at 72 characters.
6. Use the body to explain what and why, not how.

---

## Code Quality & Tooling

### Backend (Python, FastAPI)

Run these from `lsfb-website/backend` (activate your Poetry environment first):

- **ruff** – Linting and formatting:
  - Check:

    ```bash
    poetry run ruff check .
    ```

  - Format:

    ```bash
    poetry run ruff format .
    ```

- **mypy** – Static type checking:

  ```bash
  poetry run mypy --explicit-package-bases .
  ```

> **Note:** Use `--explicit-package-bases` with mypy to avoid import issues.

### Frontend (Vue.js, Vite)

Run these from `lsfb-website/frontend`:

- **stylelint** – CSS/Vue style linting:

  ```bash
  npm run stylelint:fix
  ```

- **eslint** – JS/Vue linting:

  ```bash
  npm run lint:fix
  ```

- **prettier** – Code formatting:

  ```bash
  npm run format:fix
  ```

- **i18n extract & clean** – Internationalization:
  - Extract and clean in one step (recommended, see below):

    ```bash
    npm run i18n:extract-clean
    ```

    > This script will extract i18n keys and immediately clean empty translation keys/values in one step.

  - Or run separately:

    ```bash
    npm run i18n:extract
    npm run i18n:clean-empty
    ```

    > Use this if you want more control over each step.

---

## Testing & Development

### Running Tests Using Pytest

Testing is done using **Pytest** (and **pytest-cov** for coverage). Both are managed by Poetry.

**Steps to Run the Tests:**

1. Make sure you're in the `backend` folder:

    ```bash
    cd lsfb-website/backend
    ```

2. Run the tests:

    ```bash
    poetry run pytest
    ```

   This will automatically discover and run the tests.

3. To run the tests with a coverage report:

    ```bash
    poetry run pytest --cov=. --cov-config=.coveragerc --cov-report=html:coverage/html
    ```

### Running Tests Using Vitest

Testing is done using **Vitest** (with **@vitest/coverage-v8** for coverage and **@vue/test-utils** for Vue component testing).

**Steps to Run the Tests:**

1. Make sure you're in the `frontend` folder:

    ```bash
    cd lsfb-website/frontend
    ```

2. Run the tests:

    ```bash
    npm run test
    ```

   This will run tests in watch mode by default.

3. To run the tests with a coverage report:

    ```bash
    npm run test:coverage
    ```

   This will generate coverage reports and exit after running all tests.

---

## Pull Requests

- Make sure your branch is up to date with `dev` before opening a PR.
- Ensure all checks pass (lint, tests, formatting).
- Provide a clear description of your changes and reference related issues.
- Assign reviewers if possible.

---

## Questions?

If you have any questions, [open an issue](https://github.com/lsfb/MDL-Corpus/issues) or [start a discussion](https://github.com/lsfb/MDL-Corpus/discussions).

Thank you for helping improve MDL-Corpus!
