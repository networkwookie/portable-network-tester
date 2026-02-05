# Contributing to Portable Network Tester

Thank you for considering contributing to this project! Here are some guidelines to help you get started.

## Development Setup

1. Fork and clone the repository
2. Run the setup script:
   ```bash
   ./scripts/setup.sh
   ```
3. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

## Code Quality

We use several tools to maintain code quality:

- **Black**: Code formatting
- **Ruff**: Linting
- **MyPy**: Type checking
- **Pytest**: Testing

### Before Committing

Run these checks locally:

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/

# Run tests
pytest
```

Or use pre-commit hooks (automatically runs on commit):

```bash
pre-commit install
```

## Testing

We have three levels of tests:

### Unit Tests
Test individual functions and classes in isolation.
```bash
pytest tests/unit/ -m unit
```

### Integration Tests
Test interactions between components.
```bash
pytest tests/integration/ -m integration
```

### System Tests
Test the entire application flow.
```bash
pytest tests/system/ -m system
```

### Writing Tests

- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Place system tests in `tests/system/`
- Use pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.system`
- Aim for >80% code coverage
- Mock external dependencies in unit tests

## Pull Request Process

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit:
   ```bash
   git add .
   git commit -m "Description of changes"
   ```

3. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Open a Pull Request against the `develop` branch

### PR Requirements

- All tests must pass
- Code coverage should not decrease
- Code must pass linting and type checking
- Include tests for new features
- Update documentation as needed
- Follow the existing code style

## Project Structure

```
src/
├── ui/              # User interface (Kivy)
│   ├── app.py       # Main application
│   └── screens/     # UI screens
├── tests/           # Test modules
│   ├── connectivity/
│   ├── speedtest/
│   └── capture/
└── utils/           # Utilities

tests/
├── unit/            # Unit tests
├── integration/     # Integration tests
└── system/          # System tests
```

## Adding New Features

### Adding a Test Module

1. Create module directory: `src/tests/your_module/`
2. Implement test logic with clear interface
3. Create UI screen in `src/ui/screens/`
4. Add menu button in `menu.py`
5. Write comprehensive tests
6. Update documentation

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for public functions/classes
- Keep functions focused and small
- Use meaningful variable names

## Documentation

- Update README.md for user-facing changes
- Add docstrings to new code
- Update inline comments for complex logic
- Add examples where helpful

## Issues

When creating an issue:

- Use a clear, descriptive title
- Provide steps to reproduce (for bugs)
- Include system information
- Add relevant logs or screenshots

## Questions?

Feel free to open an issue for questions or discussions!
