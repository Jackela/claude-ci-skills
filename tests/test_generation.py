import sys
import tempfile
import unittest
from pathlib import Path
import yaml
import configparser
import subprocess
from jinja2 import UndefinedError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/ci-skills-core/lib'))
from detector import ProjectDetector
from template_engine import CIConfigGenerator, TemplateEngine


class GenerationTests(unittest.TestCase):
    def test_python_and_javascript_quality_workflows(self):
        for language, manifest in [('python', 'pyproject.toml'), ('javascript', 'package.json')]:
            with self.subTest(language=language), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / manifest).write_text('{}' if language == 'javascript' else '[project]\nname="sample"')
                self.assertEqual(ProjectDetector(directory).detect_languages()['primary'], language)
                generated = CIConfigGenerator(directory, ROOT / 'skills/ci-quality-gates').generate(
                    'ci-quality-gates', ['quality-assurance.yml.j2'])
                workflow = yaml.load(generated['quality-assurance.yml'], Loader=yaml.BaseLoader)
                self.assertIn(language + '-quality', workflow['jobs'])
                self.assertIn('${{ env.', generated['quality-assurance.yml'])
                self.assertNotIn('continue-on-error', generated['quality-assurance.yml'])

    def test_python_pyramid_and_core_adapter(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / 'requirements.txt').write_text('pytest')
            generator = CIConfigGenerator(directory, ROOT / 'skills/ci-test-pyramid')
            self.assertEqual(generator.load_adapter('python')['language'], 'python')
            generated = generator.generate('ci-test-pyramid', ['ci-pyramid.yml.j2'])
            workflow = yaml.load(generated['ci-pyramid.yml'], Loader=yaml.BaseLoader)
            self.assertIn('unit-tests', workflow['jobs'])
            self.assertIn('${{ steps.pyramid.outputs.score }}', generated['ci-pyramid.yml'])

    def test_unknown_language_and_invalid_config_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            generator = CIConfigGenerator(directory, ROOT / 'skills/ci-quality-gates')
            with self.assertRaises(ValueError):
                generator.generate('ci-quality-gates', ['quality-assurance.yml.j2'])
            (Path(directory) / 'ci-skills.yaml').write_text('- wrong\n')
            with self.assertRaisesRegex(ValueError, 'mapping'):
                generator.load_config()

    def test_missing_template_variable_and_invalid_yaml_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'missing.j2').write_text('{{ missing_required_setting }}')
            with self.assertRaises(UndefinedError):
                TemplateEngine(directory).render('missing.j2', {})
            (root / 'ci-skills.yaml').write_text('project:\n  languages:\n    primary: python\n')
            templates = root / 'assets/templates'
            templates.mkdir(parents=True)
            (templates / 'broken.yml.j2').write_text('jobs: [unclosed')
            with self.assertRaises(yaml.YAMLError):
                CIConfigGenerator(directory, directory).generate('fixture', ['broken.yml.j2'])

    def test_all_templates_and_supported_quality_branches(self):
        combinations = [
            ('ci-quality-gates', 'quality-assurance.yml.j2'),
            ('ci-quality-gates', 'pre-commit-config.yaml.j2'),
            ('ci-test-pyramid', 'ci-pyramid.yml.j2'),
            ('ci-test-pyramid', 'pytest.ini.j2'),
            ('ci-local-validation', 'local-ci.sh.j2'),
        ]
        for language in ['python', 'javascript', 'go', 'rust']:
            for skill, template in combinations:
                with self.subTest(language=language, template=template), tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    (root / 'ci-skills.yaml').write_text('project:\n  languages:\n    primary: ' + language + '\n')
                    generator = CIConfigGenerator(directory, ROOT / 'skills' / skill)
                    if language != 'python' and skill == 'ci-test-pyramid':
                        with self.assertRaisesRegex(ValueError, 'requires Python'):
                            generator.generate(skill, [template])
                        continue
                    generated = generator.generate(skill, [template])
                    text = generated[template.removesuffix('.j2')]
                    if template.endswith('.ini.j2'):
                        parsed = configparser.ConfigParser()
                        parsed.read_string(text)
                        self.assertIn('--strict-markers', parsed['pytest']['addopts'])
                    elif template.endswith('.sh.j2'):
                        script = root / 'local-ci.sh'
                        script.write_text(text)
                        subprocess.run(['bash', '-n', str(script)], check=True)
                        subprocess.run(['bash', str(script), '--help'], check=True, capture_output=True)
                        self.assertIn(generator.load_adapter(language)['test']['commands']['run_unit'], text)
                        self.assertNotIn('((PASSED++))', text)
                    elif template == 'pre-commit-config.yaml.j2':
                        self.assertTrue(yaml.safe_load(text)['repos'])
                    else:
                        parsed = yaml.load(text, Loader=yaml.BaseLoader)
                        if skill == 'ci-quality-gates':
                            self.assertIn(language + '-quality', parsed['jobs'])
                            self.assertEqual(parsed['env']['NODE_VERSION'], '24')
                            if language == 'go':
                                self.assertIn("go-version: '1.27'", text)

    def test_generated_local_script_runs_all_checks_and_fails_truthfully(self):
        import os
        for language, runner in [('python', 'pytest'), ('javascript', 'npm'), ('go', 'go'), ('rust', 'cargo')]:
            with self.subTest(language=language), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / 'ci-skills.yaml').write_text('project:\n  languages:\n    primary: ' + language + '\n')
                generator = CIConfigGenerator(directory, ROOT / 'skills/ci-local-validation')
                text = generator.generate('ci-local-validation', ['local-ci.sh.j2'])['local-ci.sh']
                scripts = root / 'scripts'
                scripts.mkdir()
                script = scripts / 'local-ci.sh'
                script.write_text(text)
                bin_dir = root / 'bin'
                bin_dir.mkdir()
                for tool in ['python', 'jq', 'pytest', 'npm', 'go', 'cargo', 'flake8', 'black']:
                    stub = bin_dir / tool
                    stub.write_text('#!/bin/sh\nif [ "$FAIL_TOOL" = "' + tool + '" ]; then exit 1; fi\nexit 0\n')
                    stub.chmod(0o755)
                env = {**os.environ, 'PATH': str(bin_dir) + ':' + os.environ['PATH']}
                good = subprocess.run(['bash', str(script)], env=env, capture_output=True, text=True)
                self.assertEqual(good.returncode, 0, good.stdout + good.stderr)
                self.assertIn('CI validation PASSED', good.stdout)
                bad = subprocess.run(['bash', str(script)], env={**env, 'FAIL_TOOL': runner}, capture_output=True, text=True)
                self.assertNotEqual(bad.returncode, 0)
                self.assertIn('CI validation FAILED', bad.stdout)


if __name__ == '__main__':
    unittest.main()
