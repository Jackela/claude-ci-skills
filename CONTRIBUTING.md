# Contributing to Claude CI Skills

Thank you for your interest in contributing to Claude CI Skills!

## How to Contribute

### Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Include reproduction steps for bugs
- Describe the expected vs actual behavior

### Adding a New Skill

1. Create a new directory under `skills/`:
   ```
   skills/ci-new-skill/
   ├── SKILL.md          # Required: Core documentation
   ├── config/
   │   └── defaults.yaml # Default configuration
   ├── scripts/          # Helper scripts
   ├── assets/
   │   └── templates/    # Jinja2 templates
   └── references/       # Additional documentation
   ```

2. Follow the SKILL.md format:
   ```yaml
   ---
   name: ci-new-skill
   description: |
     Clear description of when to use this skill.
   version: 1.0.0
   allowed-tools: Read, Write, Edit, Bash, Glob, Grep
   ---

   # Skill Name

   ## Purpose
   ## When to Use
   ## Quick Setup
   ## Configuration
   ## Templates
   ```

3. Add tests for any Python scripts

4. Update the main README.md if needed

### Adding a Language Adapter

1. Create adapter directory:
   ```
   skills/ci-skills-core/adapters/new-language/
   ├── adapter.yaml
   └── scripts/
   ```

2. Implement the adapter interface in `adapter.yaml`:
   ```yaml
   language: new-language
   version_range: ">=x.y"

   indicators:
     files: [...]

   test:
     framework: ...
     commands:
       run_all: ...
       run_unit: ...

   lint:
     tools:
       - name: ...
         command: ...
   ```

3. Add detection logic to `lib/detector.py`

### Code Style

- Python: Follow PEP 8, use Black for formatting
- YAML: 2-space indentation
- Markdown: Use GitHub-flavored markdown

### Commit Messages

Use conventional commits:
- `feat: add new feature`
- `fix: resolve bug`
- `docs: update documentation`
- `chore: maintenance tasks`

### Pull Requests

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a PR with a clear description

## Development Setup

```bash
# Clone
git clone https://github.com/p3nGu1nZz/claude-ci-skills.git
cd claude-ci-skills

# Install as plugin (for testing)
claude /plugin /path/to/claude-ci-skills
```

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
