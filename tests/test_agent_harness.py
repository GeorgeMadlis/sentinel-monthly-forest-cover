"""The downstream adapter never guesses a sibling checkout or hides validator failure."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('round_adapter', ROOT / 'scripts/validate_agent_rounds.py')
ADAPTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADAPTER)


class AgentHarnessTests(unittest.TestCase):
    def test_explicit_lab_and_current_repository_forwarded(self):
        with tempfile.TemporaryDirectory(prefix='lab with spaces ') as directory:
            lab = Path(directory)
            validator = lab / 'agent_harness/scripts/validate_round.py'
            validator.parent.mkdir(parents=True)
            validator.touch()
            with patch.object(sys, 'argv', ['validate_agent_rounds.py', '--lab', str(lab)]), patch.object(ADAPTER.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)) as run:
                self.assertEqual(ADAPTER.main(), 1)
                self.assertEqual(run.call_args.args[0], [sys.executable, str(validator.resolve()), '--lab', str(lab.resolve()), '--root', str(ROOT)])
                self.assertFalse(run.call_args.kwargs['check'])

    def test_missing_lab_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/validate_agent_rounds.py'), '--lab', directory], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('must contain', result.stderr)

    def test_lab_argument_required(self):
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/validate_agent_rounds.py')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)


if __name__ == '__main__':
    unittest.main()
