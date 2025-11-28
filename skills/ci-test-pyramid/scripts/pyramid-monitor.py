#!/usr/bin/env python3
"""
Test Pyramid Monitor
====================

Monitor test pyramid distribution by parsing test files.
Supports Python (pytest), JavaScript (Vitest/Jest), Go, and Rust.

Usage:
    python pyramid-monitor.py                    # Console report
    python pyramid-monitor.py --format json      # JSON output
    python pyramid-monitor.py --format markdown  # Markdown report
    python pyramid-monitor.py --format html      # HTML report
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set


class TestPyramidMonitor:
    """Monitor test pyramid distribution across multiple languages."""

    DEFAULT_TARGETS = {
        "unit": 70.0,
        "integration": 20.0,
        "e2e": 10.0,
    }

    def __init__(
        self,
        project_root: Path = None,
        targets: Dict[str, float] = None,
        minimum_score: float = 5.5,
    ):
        """Initialize monitor."""
        self.project_root = project_root or Path.cwd()
        self.targets = targets or self.DEFAULT_TARGETS
        self.minimum_score = minimum_score
        self.history_dir = self.project_root / ".pyramid-history"

        self.tests_by_marker: Dict[str, Set[str]] = {
            "unit": set(),
            "integration": set(),
            "e2e": set(),
        }
        self.all_tests: Set[str] = set()
        self.test_files_scanned = 0
        self.language: Optional[str] = None

    def detect_language(self) -> str:
        """Detect primary project language."""
        if (self.project_root / "pyproject.toml").exists() or (
            self.project_root / "pytest.ini"
        ).exists():
            return "python"
        if (self.project_root / "package.json").exists():
            return "javascript"
        if (self.project_root / "go.mod").exists():
            return "go"
        if (self.project_root / "Cargo.toml").exists():
            return "rust"
        return "python"  # Default

    def collect_tests(self) -> bool:
        """Collect tests by scanning test files."""
        self.language = self.detect_language()
        print(f"Detected language: {self.language}", file=sys.stderr)

        if self.language == "python":
            return self._collect_python_tests()
        elif self.language == "javascript":
            return self._collect_javascript_tests()
        elif self.language == "go":
            return self._collect_go_tests()
        elif self.language == "rust":
            return self._collect_rust_tests()

        return False

    def _collect_python_tests(self) -> bool:
        """Collect Python (pytest) tests."""
        tests_dir = self.project_root / "tests"
        if not tests_dir.exists():
            # Try src layout
            tests_dir = self.project_root / "src" / "tests"
            if not tests_dir.exists():
                print(f"Error: tests directory not found", file=sys.stderr)
                return False

        test_files = list(tests_dir.rglob("test_*.py"))
        self.test_files_scanned = len(test_files)
        print(f"Found {len(test_files)} test files", file=sys.stderr)

        for test_file in test_files:
            self._parse_python_test_file(test_file)

        print(f"Collected {len(self.all_tests)} tests total", file=sys.stderr)
        return True

    def _parse_python_test_file(self, file_path: Path) -> None:
        """Parse a Python test file for markers."""
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.split("\n")

            class_markers = set()
            function_markers = set()
            current_class = None

            for i, line in enumerate(lines):
                # Check for class definition
                class_match = re.match(r"^class (Test\w+)", line)
                if class_match:
                    current_class = class_match.group(1)
                    class_markers = set()
                    function_markers = set()
                    # Look back for class markers
                    for j in range(max(0, i - 10), i):
                        marker = re.search(
                            r"@pytest\.mark\.(unit|integration|e2e)", lines[j]
                        )
                        if marker:
                            class_markers.add(marker.group(1))

                # Check for function markers
                if line.strip().startswith("@pytest.mark."):
                    marker = re.search(r"@pytest\.mark\.(unit|integration|e2e)", line)
                    if marker:
                        function_markers.add(marker.group(1))

                # Check for test function
                test_match = re.match(r"^    def (test_\w+)", line)
                if test_match:
                    test_name = test_match.group(1)
                    test_id = f"{file_path.relative_to(self.project_root)}::{current_class or ''}{test_name}"

                    self.all_tests.add(test_id)

                    effective_markers = class_markers | function_markers
                    for marker in effective_markers:
                        if marker in self.tests_by_marker:
                            self.tests_by_marker[marker].add(test_id)

                    function_markers = set()

        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}", file=sys.stderr)

    def _collect_javascript_tests(self) -> bool:
        """Collect JavaScript/TypeScript tests."""
        # Look for test directories
        test_dirs = ["tests", "test", "__tests__", "src/__tests__"]
        test_files = []

        for test_dir in test_dirs:
            dir_path = self.project_root / test_dir
            if dir_path.exists():
                test_files.extend(dir_path.rglob("*.test.ts"))
                test_files.extend(dir_path.rglob("*.test.js"))
                test_files.extend(dir_path.rglob("*.spec.ts"))
                test_files.extend(dir_path.rglob("*.spec.js"))

        self.test_files_scanned = len(test_files)
        print(f"Found {len(test_files)} test files", file=sys.stderr)

        for test_file in test_files:
            self._parse_javascript_test_file(test_file)

        print(f"Collected {len(self.all_tests)} tests total", file=sys.stderr)
        return True

    def _parse_javascript_test_file(self, file_path: Path) -> None:
        """Parse a JavaScript/TypeScript test file."""
        try:
            content = file_path.read_text(encoding="utf-8")

            # Find describe blocks with tags
            describe_pattern = re.compile(
                r"describe\(['\"](\w+):\s*(.+?)['\"]", re.MULTILINE
            )
            test_pattern = re.compile(
                r"(?:test|it)\(['\"](.+?)['\"]", re.MULTILINE
            )

            current_category = None

            for match in describe_pattern.finditer(content):
                category = match.group(1).lower()
                if category in self.tests_by_marker:
                    current_category = category

            # Find all tests
            for match in test_pattern.finditer(content):
                test_name = match.group(1)
                test_id = f"{file_path.relative_to(self.project_root)}::{test_name}"
                self.all_tests.add(test_id)

                if current_category:
                    self.tests_by_marker[current_category].add(test_id)

        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}", file=sys.stderr)

    def _collect_go_tests(self) -> bool:
        """Collect Go tests."""
        test_files = list(self.project_root.rglob("*_test.go"))
        self.test_files_scanned = len(test_files)
        print(f"Found {len(test_files)} test files", file=sys.stderr)

        for test_file in test_files:
            self._parse_go_test_file(test_file)

        print(f"Collected {len(self.all_tests)} tests total", file=sys.stderr)
        return True

    def _parse_go_test_file(self, file_path: Path) -> None:
        """Parse a Go test file."""
        try:
            content = file_path.read_text(encoding="utf-8")

            # Find test functions
            test_pattern = re.compile(r"func (Test\w+)\(", re.MULTILINE)

            for match in test_pattern.finditer(content):
                test_name = match.group(1)
                test_id = f"{file_path.relative_to(self.project_root)}::{test_name}"
                self.all_tests.add(test_id)

                # Check for build tags in comments above
                pos = match.start()
                before = content[:pos]
                lines_before = before.split("\n")[-5:]

                for line in lines_before:
                    if "// +build unit" in line or "//go:build unit" in line:
                        self.tests_by_marker["unit"].add(test_id)
                    elif "// +build integration" in line or "//go:build integration" in line:
                        self.tests_by_marker["integration"].add(test_id)
                    elif "// +build e2e" in line or "//go:build e2e" in line:
                        self.tests_by_marker["e2e"].add(test_id)

        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}", file=sys.stderr)

    def _collect_rust_tests(self) -> bool:
        """Collect Rust tests."""
        test_files = list(self.project_root.rglob("*.rs"))
        self.test_files_scanned = len(test_files)
        print(f"Found {len(test_files)} Rust files", file=sys.stderr)

        for test_file in test_files:
            self._parse_rust_test_file(test_file)

        print(f"Collected {len(self.all_tests)} tests total", file=sys.stderr)
        return True

    def _parse_rust_test_file(self, file_path: Path) -> None:
        """Parse a Rust test file."""
        try:
            content = file_path.read_text(encoding="utf-8")

            # Find test functions
            test_pattern = re.compile(r"#\[test\]\s*fn (\w+)", re.MULTILINE)

            for match in test_pattern.finditer(content):
                test_name = match.group(1)
                test_id = f"{file_path.relative_to(self.project_root)}::{test_name}"
                self.all_tests.add(test_id)

                # Check for category comments
                pos = match.start()
                before = content[:pos]
                lines_before = before.split("\n")[-5:]

                for line in lines_before:
                    if "// unit" in line.lower():
                        self.tests_by_marker["unit"].add(test_id)
                    elif "// integration" in line.lower():
                        self.tests_by_marker["integration"].add(test_id)
                    elif "// e2e" in line.lower():
                        self.tests_by_marker["e2e"].add(test_id)

        except Exception as e:
            print(f"Warning: Could not parse {file_path}: {e}", file=sys.stderr)

    def calculate_distribution(self) -> Dict[str, float]:
        """Calculate percentage distribution."""
        total = len(self.all_tests)
        if total == 0:
            return {marker: 0.0 for marker in self.targets}

        distribution = {}
        for marker in self.targets:
            count = len(self.tests_by_marker[marker])
            distribution[marker] = (count / total) * 100

        return distribution

    def calculate_score(self, distribution: Dict[str, float]) -> float:
        """Calculate pyramid score (0-10)."""
        score = 10.0

        for marker, target in self.targets.items():
            actual = distribution[marker]
            deviation = abs(actual - target)
            penalty = deviation * 0.1
            score -= penalty

        # Penalty for uncategorized tests
        categorized = sum(len(tests) for tests in self.tests_by_marker.values())
        uncategorized = len(self.all_tests) - categorized
        if uncategorized > 0 and len(self.all_tests) > 0:
            uncategorized_pct = (uncategorized / len(self.all_tests)) * 100
            score -= uncategorized_pct * 0.2

        return max(0.0, min(10.0, score))

    def get_missing_markers_count(self) -> int:
        """Get count of tests without pyramid markers."""
        categorized = set()
        for tests in self.tests_by_marker.values():
            categorized.update(tests)
        return len(self.all_tests - categorized)

    def generate_console_report(
        self, distribution: Dict[str, float], score: float
    ) -> str:
        """Generate ASCII console report."""
        lines = []
        lines.append("=" * 80)
        lines.append(" " * 25 + "TEST PYRAMID REPORT")
        lines.append("=" * 80)
        lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Language: {self.language}")
        lines.append(f"Score: {score:.1f}/10.0 (minimum: {self.minimum_score})")
        status = "PASS" if score >= self.minimum_score else "FAIL"
        lines.append(f"Status: {status}")
        lines.append("")
        lines.append("DISTRIBUTION:")

        for marker in ["unit", "integration", "e2e"]:
            count = len(self.tests_by_marker[marker])
            pct = distribution[marker]
            target = self.targets[marker]
            delta = pct - target

            bar_length = 20
            filled = int((pct / 100) * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            delta_str = f"{delta:+.1f}%" if delta != 0 else " 0.0%"

            lines.append(
                f"  {marker.capitalize():14} {count:5,} ({pct:5.1f}%)  "
                f"[Target: {target:4.0f}%]  {bar}  {delta_str}"
            )

        lines.append("")
        lines.append(f"TOTAL: {len(self.all_tests):,} tests in {self.test_files_scanned} files")

        missing = self.get_missing_markers_count()
        if missing > 0:
            lines.append(f"UNCATEGORIZED: {missing} tests need classification")

        lines.append("")
        lines.append("RECOMMENDATIONS:")
        recommendations = self._generate_recommendations(distribution)
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"  {i}. {rec}")

        lines.append("=" * 80)
        return "\n".join(lines)

    def generate_json_report(self, distribution: Dict[str, float], score: float) -> str:
        """Generate JSON report."""
        data = {
            "timestamp": datetime.now().isoformat(),
            "language": self.language,
            "score": round(score, 2),
            "minimum_score": self.minimum_score,
            "passed": score >= self.minimum_score,
            "total_tests": len(self.all_tests),
            "test_files_scanned": self.test_files_scanned,
            "distribution": {
                marker: {
                    "count": len(self.tests_by_marker[marker]),
                    "percentage": round(pct, 2),
                    "target": self.targets[marker],
                    "delta": round(pct - self.targets[marker], 2),
                }
                for marker, pct in distribution.items()
            },
            "missing_markers": self.get_missing_markers_count(),
            "recommendations": self._generate_recommendations(distribution),
        }
        return json.dumps(data, indent=2)

    def generate_markdown_report(
        self, distribution: Dict[str, float], score: float
    ) -> str:
        """Generate Markdown report."""
        lines = []
        status = "✅ PASS" if score >= self.minimum_score else "❌ FAIL"

        lines.append("# Test Pyramid Report")
        lines.append("")
        lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Language:** {self.language}")
        lines.append(f"**Score:** {score:.1f}/10.0 (minimum: {self.minimum_score})")
        lines.append(f"**Status:** {status}")
        lines.append("")
        lines.append("## Distribution")
        lines.append("")
        lines.append("| Type | Count | Percentage | Target | Delta |")
        lines.append("|------|-------|------------|--------|-------|")

        for marker in ["unit", "integration", "e2e"]:
            count = len(self.tests_by_marker[marker])
            pct = distribution[marker]
            target = self.targets[marker]
            delta = pct - target

            lines.append(
                f"| {marker.capitalize()} | {count:,} | {pct:.1f}% | {target:.0f}% | {delta:+.1f}% |"
            )

        lines.append("")
        lines.append(f"**Total:** {len(self.all_tests):,} tests in {self.test_files_scanned} files")

        missing = self.get_missing_markers_count()
        if missing > 0:
            lines.append(f"**Uncategorized:** {missing} tests need classification")

        lines.append("")
        lines.append("## Recommendations")
        lines.append("")
        for i, rec in enumerate(self._generate_recommendations(distribution), 1):
            lines.append(f"{i}. {rec}")

        return "\n".join(lines)

    def _generate_recommendations(self, distribution: Dict[str, float]) -> List[str]:
        """Generate recommendations."""
        recommendations = []

        missing = self.get_missing_markers_count()
        if missing > 0:
            recommendations.append(
                f"Add pyramid markers to {missing} uncategorized tests"
            )

        for marker, target in self.targets.items():
            actual = distribution[marker]
            delta = actual - target

            if abs(delta) > 5:
                if delta > 0:
                    recommendations.append(
                        f"Consider reducing {marker} tests ({delta:+.1f}% above {target}% target)"
                    )
                else:
                    recommendations.append(
                        f"Add more {marker} tests ({abs(delta):.1f}% below {target}% target)"
                    )

        if distribution["unit"] < 60:
            recommendations.append("Unit test coverage is low - aim for 70% of tests")

        if distribution["e2e"] > 15:
            recommendations.append("E2E tests may be over-represented - keep focused on critical paths")

        if not recommendations:
            recommendations.append("Test pyramid looks healthy! Keep up the good work.")

        return recommendations


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test pyramid monitor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--format",
        choices=["console", "json", "markdown", "html"],
        default="console",
        help="Output format (default: console)",
    )
    parser.add_argument(
        "--minimum-score",
        type=float,
        default=5.5,
        help="Minimum passing score (default: 5.5)",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file (default: stdout)",
    )
    parser.add_argument(
        "--unit-target",
        type=float,
        default=70.0,
        help="Target percentage for unit tests (default: 70)",
    )
    parser.add_argument(
        "--integration-target",
        type=float,
        default=20.0,
        help="Target percentage for integration tests (default: 20)",
    )
    parser.add_argument(
        "--e2e-target",
        type=float,
        default=10.0,
        help="Target percentage for e2e tests (default: 10)",
    )

    args = parser.parse_args()

    targets = {
        "unit": args.unit_target,
        "integration": args.integration_target,
        "e2e": args.e2e_target,
    }

    monitor = TestPyramidMonitor(targets=targets, minimum_score=args.minimum_score)

    if not monitor.collect_tests():
        sys.exit(1)

    distribution = monitor.calculate_distribution()
    score = monitor.calculate_score(distribution)

    # Generate report
    if args.format == "console":
        report = monitor.generate_console_report(distribution, score)
    elif args.format == "json":
        report = monitor.generate_json_report(distribution, score)
    elif args.format == "markdown":
        report = monitor.generate_markdown_report(distribution, score)
    else:
        report = monitor.generate_console_report(distribution, score)

    # Output
    if args.output:
        Path(args.output).write_text(report)
        print(f"Report saved to {args.output}", file=sys.stderr)
    else:
        print(report)

    # Exit code based on score
    if score < args.minimum_score:
        sys.exit(1)


if __name__ == "__main__":
    main()
