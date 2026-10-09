import sys
import tempfile
import unittest
from pathlib import Path
import yaml
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


if __name__ == '__main__':
    unittest.main()
