#!/usr/bin/env python3
"""
Jinja2 Template Engine for CI Skills

Processes .j2 templates to generate CI configuration files.
"""

import re
import copy
from pathlib import Path
from typing import Any, Optional

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape, StrictUndefined
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
            undefined=StrictUndefined,
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
        # GitHub expressions are evaluated by Actions, never by Jinja.
        source, _, _ = self.env.loader.get_source(self.env, template_name)
        expressions = []
        def preserve(match):
            expressions.append(match.group(0))
            return f"__GITHUB_EXPRESSION_{len(expressions) - 1}__"
        source = re.sub(r"\$\{\{.*?\}\}", preserve, source, flags=re.DOTALL)
        rendered = self.env.from_string(source).render(**context)
        for index, expression in enumerate(expressions):
            rendered = rendered.replace(f"__GITHUB_EXPRESSION_{index}__", expression)
        return rendered

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
        self.core_dir = self.skill_dir.parent / "ci-skills-core"

    def load_config(self) -> dict:
        """Load project's ci-skills.yaml configuration."""
        import yaml

        def merge(base, override):
            for key, value in override.items():
                if isinstance(value, dict) and isinstance(base.get(key), dict):
                    merge(base[key], value)
                else:
                    base[key] = copy.deepcopy(value)
            return base

        config = {}
        for path in [self.core_dir / "config/defaults.yaml", self.project_root / "ci-skills.yaml"]:
            if path.exists():
                loaded = yaml.safe_load(path.read_text()) or {}
                if not isinstance(loaded, dict):
                    raise ValueError(f"Configuration must be a mapping: {path}")
                merge(config, loaded)
        # Published YAML uses hyphenated names; templates use Python identifiers.
        for key, value in list(config.items()):
            config[key.replace("-", "_")] = value
        if not config.get("project", {}).get("languages", {}).get("primary"):
            from detector import ProjectDetector
            config.setdefault("project", {})["languages"] = ProjectDetector(str(self.project_root)).detect_languages()
        primary = config["project"]["languages"].get("primary")
        if primary not in {"python", "javascript", "go", "rust"}:
            raise ValueError("No supported primary language detected; configure project.languages.primary")
        config.setdefault("quality_gates", {}).setdefault("python", {})
        return config

    def load_adapter(self, language: str) -> dict:
        """Load language adapter configuration."""
        import yaml

        adapter_path = self.core_dir / "adapters" / language / "adapter.yaml"
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
            if output_name.endswith((".yml", ".yaml")):
                import yaml
                parsed = yaml.load(content, Loader=yaml.BaseLoader)
                if not isinstance(parsed, dict):
                    raise ValueError(f"Generated YAML must be a mapping: {output_name}")
                if output_name.endswith(".yml") and (not parsed.get("jobs") or not parsed.get("on")):
                    raise ValueError(f"Generated workflow lacks triggers/jobs: {output_name}")
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
