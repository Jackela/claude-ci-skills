#!/usr/bin/env python3
"""
Jinja2 Template Engine for CI Skills

Processes .j2 templates to generate CI configuration files.
"""

import os
from pathlib import Path
from typing import Any, Optional

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    print("Jinja2 not installed. Run: pip install jinja2")
    raise


class TemplateEngine:
    """Jinja2 template processor for CI configurations."""

    def __init__(self, templates_dir: str):
        self.templates_dir = Path(templates_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        # Add custom filters
        self.env.filters["yaml_indent"] = self._yaml_indent
        self.env.filters["to_yaml_list"] = self._to_yaml_list

    @staticmethod
    def _yaml_indent(text: str, width: int = 2, first: bool = False) -> str:
        """Indent text for YAML embedding."""
        lines = text.split("\n")
        if not first:
            lines[0] = lines[0]  # Don't indent first line
            lines[1:] = [" " * width + line for line in lines[1:]]
        else:
            lines = [" " * width + line for line in lines]
        return "\n".join(lines)

    @staticmethod
    def _to_yaml_list(items: list, indent: int = 0) -> str:
        """Convert list to YAML format."""
        prefix = " " * indent
        return "\n".join(f"{prefix}- {item}" for item in items)

    def render(self, template_name: str, context: dict) -> str:
        """
        Render a template with the given context.

        Args:
            template_name: Name of the template file (e.g., 'ci.yml.j2')
            context: Dictionary of variables to pass to template

        Returns:
            Rendered template content
        """
        template = self.env.get_template(template_name)
        return template.render(**context)

    def render_to_file(
        self, template_name: str, output_path: str, context: dict
    ) -> None:
        """
        Render a template and write to file.

        Args:
            template_name: Name of the template file
            output_path: Path to write the output
            context: Dictionary of variables
        """
        content = self.render(template_name, context)
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content)

    def list_templates(self) -> list:
        """List all available templates."""
        return [str(p.name) for p in self.templates_dir.glob("*.j2")]


class CIConfigGenerator:
    """High-level CI configuration generator."""

    def __init__(self, project_root: str, skill_dir: str):
        self.project_root = Path(project_root)
        self.skill_dir = Path(skill_dir)

    def load_config(self) -> dict:
        """Load project's ci-skills.yaml configuration."""
        import yaml

        config_path = self.project_root / "ci-skills.yaml"
        if config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f)

        # Load defaults
        defaults_path = self.skill_dir / "config" / "defaults.yaml"
        if defaults_path.exists():
            with open(defaults_path) as f:
                return yaml.safe_load(f)

        return {}

    def load_adapter(self, language: str) -> dict:
        """Load language adapter configuration."""
        import yaml

        adapter_path = self.skill_dir / "adapters" / language / "adapter.yaml"
        if adapter_path.exists():
            with open(adapter_path) as f:
                return yaml.safe_load(f)
        return {}

    def build_context(self, config: dict, adapters: dict) -> dict:
        """Build template context from config and adapters."""
        return {
            "project": config.get("project", {}),
            "config": config,
            "adapters": adapters,
            # Helper values
            "python_version": config.get("github_actions", {}).get(
                "python_version", "3.11"
            ),
            "node_version": config.get("github_actions", {}).get("node_version", "20"),
            "go_version": config.get("github_actions", {}).get("go_version", "1.21"),
        }

    def generate(self, skill_name: str, templates: list) -> dict:
        """
        Generate CI configurations for a skill.

        Args:
            skill_name: Name of the skill (e.g., 'ci-test-pyramid')
            templates: List of template names to process

        Returns:
            Dict mapping output paths to generated content
        """
        config = self.load_config()
        languages = config.get("project", {}).get("languages", {})

        # Load adapters
        adapters = {}
        primary = languages.get("primary", "python")
        adapters[primary] = self.load_adapter(primary)
        for lang in languages.get("secondary", []):
            adapters[lang] = self.load_adapter(lang)

        context = self.build_context(config, adapters)

        # Process templates
        templates_dir = self.skill_dir / "assets" / "templates"
        engine = TemplateEngine(str(templates_dir))

        results = {}
        for template in templates:
            output_name = template.replace(".j2", "")
            content = engine.render(template, context)
            results[output_name] = content

        return results


def main():
    """CLI entry point for testing."""
    import sys

    if len(sys.argv) < 3:
        print("Usage: template_engine.py <templates_dir> <template_name> [output_file]")
        sys.exit(1)

    templates_dir = sys.argv[1]
    template_name = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None

    engine = TemplateEngine(templates_dir)

    # Sample context for testing
    context = {
        "project": {"name": "test-project"},
        "config": {"test_pyramid": {"targets": {"unit": 70, "integration": 20, "e2e": 10}}},
    }

    content = engine.render(template_name, context)

    if output_file:
        Path(output_file).write_text(content)
        print(f"Written to {output_file}")
    else:
        print(content)


if __name__ == "__main__":
    main()
