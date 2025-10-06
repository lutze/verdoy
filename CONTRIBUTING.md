# Contributing to VerdoyLab

Thank you for your interest in contributing to VerdoyLab! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Docker and Docker Compose
- Git
- Node.js (for frontend testing)

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/lms-core-poc.git
   cd lms-core-poc
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your development configuration
   ```

3. **Start development environment**
   ```bash
   docker compose up -d
   ```

4. **Install development dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

## 🛠️ Development Workflow

### Code Style

- Follow PEP 8 for Python code
- Use type hints for all functions
- Write docstrings for all public functions and classes
- Use meaningful variable and function names

### Testing

- Write tests for new features
- Ensure all tests pass before submitting
- Aim for good test coverage

```bash
# Run backend tests
cd backend
pytest

# Run frontend tests
npm test
```

### Database Changes

- All database changes must be in migration files
- Migration files should be in `database/migrations/`
- Include both forward and rollback migrations
- Test migrations on a copy of production data

### API Changes

- Update OpenAPI documentation
- Maintain backward compatibility when possible
- Add proper error handling and validation
- Include example requests/responses

## 📝 Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, well-documented code
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   # Run the full test suite
   docker compose down
   docker compose up -d --build
   # Run tests
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add: brief description of changes"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

### Pull Request Guidelines

- Provide a clear description of changes
- Reference any related issues
- Include screenshots for UI changes
- Ensure CI/CD checks pass
- Request review from maintainers

## 🐛 Bug Reports

When reporting bugs, please include:

- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, etc.)
- Screenshots if applicable

## 💡 Feature Requests

For feature requests, please:

- Describe the feature clearly
- Explain the use case
- Consider implementation complexity
- Check for existing similar requests

## 📋 Issue Labels

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Improvements to documentation
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed
- `question`: Further information is requested

## 🏗️ Architecture Guidelines

### Backend

- Use async/await for database operations
- Follow the service layer pattern
- Implement proper error handling
- Use Pydantic for data validation
- Follow RESTful API conventions

### Frontend

- Use server-side rendering with Jinja2
- Progressive enhancement with minimal JavaScript
- Follow the design system in `backend/app/static/css/`
- Ensure accessibility compliance

### Database

- Use single-table inheritance for entities
- Implement proper indexing
- Follow event sourcing patterns
- Maintain audit trails

## 🔒 Security

- Never commit secrets or credentials
- Use environment variables for configuration
- Validate all user inputs
- Follow OWASP security guidelines
- Report security issues privately

## 📚 Documentation

- Update README.md for significant changes
- Document new API endpoints
- Include code examples
- Keep architecture documentation current

## 🎯 Code Review Process

- Be respectful and constructive
- Focus on code quality and functionality
- Test the changes locally
- Provide specific feedback
- Approve when ready

## 📞 Getting Help

- Check existing issues and discussions
- Join our community discussions
- Ask questions in GitHub Discussions
- Contact maintainers for urgent issues

## 📄 License

By contributing, you agree that your contributions will be licensed under the GNU Affero General Public License v3.0.

Thank you for contributing to VerdoyLab! 🎉
