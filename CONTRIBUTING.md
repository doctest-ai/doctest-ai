# Contributing to doctest-ai

Thank you for your interest in contributing to doctest-ai! We welcome contributions from the community and are excited to see how you can help improve this project.

## Ways to Contribute

There are many ways you can contribute to doctest-ai:

### Add More Examples

Examples are crucial for helping users understand how to use doctest-ai effectively. You can contribute by:

- Creating new examples for different frameworks and tools
- Improving existing examples with better documentation
- Adding edge cases or advanced usage patterns to existing examples

Examples should be placed in the `examples/` directory and follow the structure of existing examples (a `.feature` file and corresponding test implementation).

### Add Support for More Coding Agents

Currently, doctest-ai supports Claude Code. We'd love to see support for other coding agents! If you're interested in adding support for a new agent:

1. Check existing issues to see if someone is already working on it
2. Open an issue to discuss your approach before starting work
3. Implement the integration following the existing patterns
4. Add documentation and examples

### Add Documentation

Documentation improvements are always welcome:

- Fix typos or clarify existing documentation
- Add tutorials or how-to guides
- Improve API documentation
- Add diagrams or visual aids
- Translate documentation to other languages

### Add Tests

Help us improve test coverage:

- Add unit tests for core functionality
- Add integration tests for new features
- Improve existing test cases
- Add edge case testing

### Provide Feedback

Your feedback helps us improve:

- Report bugs by opening an issue
- Suggest new features or improvements
- Share your use cases and experiences
- Participate in discussions on existing issues

## Development Setup

To set up your development environment:

1. **Install prerequisites**:
   - [Claude Code](https://code.claude.com/docs/en/setup)
   - [uv](https://docs.astral.sh/uv/getting-started/installation/)

2. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/doctest-ai.git
   cd doctest-ai
   ```

3. **Create a virtual environment and install dependencies**:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv sync
   ```

## Code Contribution Guidelines

### Before You Start

- Check existing issues and pull requests to avoid duplicate work
- For major changes, open an issue first to discuss your approach
- Make sure you're working on the latest version of the main branch

### Commit Messages

- Use clear and descriptive commit messages (follow the [Conventional Commits specification](https://www.conventionalcommits.org/en/v1.0.0/))
- Start with a verb in the imperative mood (e.g., "add", "fix", "update")

## Code of Conduct

This project follows a code of conduct to ensure a welcoming environment for all contributors. Please be respectful and constructive in all interactions.

## License

By contributing to doctest-ai, you agree that your contributions will be licensed under the Apache License 2.0.

---

Thank you for contributing to doctest-ai!
