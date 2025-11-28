#!/usr/bin/env python3
"""
Language and Framework Detector

Detects project languages and frameworks by scanning for indicator files.
Used by CI Skills to automatically configure appropriate tools.
"""

import os
from pathlib import Path
from typing import Optional


class ProjectDetector:
    """Detects project languages and frameworks."""

    LANGUAGE_INDICATORS = {
        "python": {
            "files": ["pyproject.toml", "setup.py", "requirements.txt", "Pipfile"],
            "extensions": [".py"],
            "weight": 0,
        },
        "javascript": {
            "files": ["package.json", "tsconfig.json"],
            "extensions": [".js", ".jsx", ".ts", ".tsx"],
            "weight": 0,
        },
        "go": {
            "files": ["go.mod", "go.sum"],
            "extensions": [".go"],
            "weight": 0,
        },
        "rust": {
            "files": ["Cargo.toml", "Cargo.lock"],
            "extensions": [".rs"],
            "weight": 0,
        },
    }

    FRAMEWORK_INDICATORS = {
        # Python frameworks
        "pytest": ["pytest.ini", "conftest.py", "pyproject.toml"],
        "django": ["manage.py", "settings.py"],
        "fastapi": ["main.py"],  # Check imports
        "flask": ["app.py"],
        # JavaScript frameworks
        "react": ["package.json"],  # Check dependencies
        "vue": ["package.json"],
        "vitest": ["vitest.config.ts", "vitest.config.js"],
        "jest": ["jest.config.js", "jest.config.ts"],
        "playwright": ["playwright.config.ts", "playwright.config.js"],
        # Go frameworks
        "gin": ["go.mod"],  # Check imports
        "echo": ["go.mod"],
    }

    def __init__(self, project_root: str = "."):
        self.root = Path(project_root).resolve()

    def detect_languages(self) -> dict:
        """
        Detect languages used in the project.

        Returns:
            dict with 'primary' and 'secondary' languages
        """
        scores = {}

        for lang, indicators in self.LANGUAGE_INDICATORS.items():
            score = 0

            # Check indicator files
            for file in indicators["files"]:
                if (self.root / file).exists():
                    score += 10

            # Count files with language extensions
            for ext in indicators["extensions"]:
                count = len(list(self.root.rglob(f"*{ext}")))
                # Exclude common directories
                count = sum(
                    1
                    for f in self.root.rglob(f"*{ext}")
                    if "node_modules" not in str(f)
                    and ".venv" not in str(f)
                    and "target" not in str(f)
                    and "__pycache__" not in str(f)
                )
                score += min(count, 50)  # Cap at 50

            if score > 0:
                scores[lang] = score

        if not scores:
            return {"primary": None, "secondary": []}

        # Sort by score
        sorted_langs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_langs[0][0]
        secondary = [lang for lang, _ in sorted_langs[1:] if scores[lang] >= 10]

        return {"primary": primary, "secondary": secondary}

    def detect_test_framework(self, language: str) -> Optional[str]:
        """Detect the test framework for a given language."""
        if language == "python":
            if (self.root / "pytest.ini").exists() or (
                self.root / "conftest.py"
            ).exists():
                return "pytest"
            # Check pyproject.toml for pytest config
            pyproject = self.root / "pyproject.toml"
            if pyproject.exists() and "pytest" in pyproject.read_text():
                return "pytest"
            return "pytest"  # Default for Python

        elif language == "javascript":
            if any(
                (self.root / f).exists()
                for f in ["vitest.config.ts", "vitest.config.js"]
            ):
                return "vitest"
            if any(
                (self.root / f).exists()
                for f in ["jest.config.js", "jest.config.ts", "jest.config.json"]
            ):
                return "jest"
            # Check package.json
            pkg = self.root / "package.json"
            if pkg.exists():
                content = pkg.read_text()
                if "vitest" in content:
                    return "vitest"
                if "jest" in content:
                    return "jest"
            return "vitest"  # Default for JS

        elif language == "go":
            return "go test"

        elif language == "rust":
            return "cargo test"

        return None

    def detect_frontend_framework(self) -> Optional[str]:
        """Detect frontend framework (React, Vue, etc.)."""
        pkg = self.root / "package.json"
        if not pkg.exists():
            return None

        content = pkg.read_text()

        if '"react"' in content or '"react-dom"' in content:
            return "react"
        if '"vue"' in content:
            return "vue"
        if '"svelte"' in content:
            return "svelte"
        if '"@angular/core"' in content:
            return "angular"

        return None

    def has_frontend(self) -> bool:
        """Check if project has a frontend component."""
        indicators = [
            self.root / "frontend",
            self.root / "client",
            self.root / "src" / "components",
            self.root / "pages",
            self.root / "app",
        ]
        return any(d.is_dir() for d in indicators) or self.detect_frontend_framework()

    def has_docker(self) -> bool:
        """Check if project uses Docker."""
        return (self.root / "Dockerfile").exists() or (
            self.root / "docker-compose.yml"
        ).exists()

    def has_kubernetes(self) -> bool:
        """Check if project uses Kubernetes."""
        k8s_indicators = ["k8s", "kubernetes", "helm", "kustomization.yaml"]
        return any((self.root / ind).exists() for ind in k8s_indicators)

    def get_full_report(self) -> dict:
        """Get a complete detection report."""
        languages = self.detect_languages()
        primary = languages["primary"]

        return {
            "languages": languages,
            "test_framework": self.detect_test_framework(primary) if primary else None,
            "frontend_framework": self.detect_frontend_framework(),
            "has_frontend": self.has_frontend(),
            "has_docker": self.has_docker(),
            "has_kubernetes": self.has_kubernetes(),
            "root": str(self.root),
        }


def main():
    """CLI entry point."""
    import json
    import sys

    root = sys.argv[1] if len(sys.argv) > 1 else "."
    detector = ProjectDetector(root)
    report = detector.get_full_report()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
