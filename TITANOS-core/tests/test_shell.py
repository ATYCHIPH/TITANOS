import unittest
from unittest.mock import patch, MagicMock
import subprocess
import os
import tempfile
import titanos.platform.shell as shell_module
from titanos.platform.shell import Shell

class TestShell(unittest.TestCase):
    def test_get_default_shell_windows(self):
        original_system = shell_module.platform.system
        original_has_command = Shell.has_command
        try:
            shell_module.platform.system = lambda: "Windows"

            Shell.has_command = staticmethod(lambda cmd: cmd == "pwsh")
            self.assertEqual(Shell.get_default_shell(), "pwsh")

            Shell.has_command = staticmethod(lambda cmd: cmd == "powershell")
            self.assertEqual(Shell.get_default_shell(), "powershell")

            Shell.has_command = staticmethod(lambda cmd: False)
            self.assertEqual(Shell.get_default_shell(), "cmd")
        finally:
            shell_module.platform.system = original_system
            Shell.has_command = original_has_command

    def test_get_default_shell_unix(self):
        original_system = shell_module.platform.system
        original_has_command = Shell.has_command
        try:
            shell_module.platform.system = lambda: "Linux"

            Shell.has_command = staticmethod(lambda cmd: cmd == "bash")
            self.assertEqual(Shell.get_default_shell(), "bash")

            Shell.has_command = staticmethod(lambda cmd: False)
            self.assertEqual(Shell.get_default_shell(), "sh")
        finally:
            shell_module.platform.system = original_system
            Shell.has_command = original_has_command

    @patch('subprocess.run')
    @patch('titanos.platform.shell.Shell.get_default_shell')
    def test_execute_one_retry_means_two_attempts(self, mock_get_shell, mock_run):
        mock_get_shell.return_value = "cmd"
        # Create mock failed responses
        fail_response = MagicMock()
        fail_response.returncode = 1
        
        success_response = MagicMock()
        success_response.returncode = 0
        
        # 1 retry = 2 total attempts. Fails then succeeds.
        mock_run.side_effect = [fail_response, success_response]
        
        # We set backoff to 0 to make the test fast
        result = Shell.execute("echo test", retries=1, backoff=0.0)
        
        self.assertEqual(result.returncode, 0)
        self.assertEqual(mock_run.call_count, 2)
        
    @patch('subprocess.run')
    @patch('titanos.platform.shell.Shell.get_default_shell')
    def test_execute_retries_exhausted(self, mock_get_shell, mock_run):
        mock_get_shell.return_value = "cmd"
        # Create a mock failed response
        fail_response = MagicMock()
        fail_response.returncode = 1
        
        # 2 retries = 3 total attempts
        mock_run.side_effect = [fail_response, fail_response, fail_response]
        
        result = Shell.execute("echo test", retries=2, backoff=0.0)
        
        self.assertEqual(result.returncode, 1)
        self.assertEqual(mock_run.call_count, 3)

    def test_run_hook(self):
        # Create a temporary directory with dummy hooks
        with tempfile.TemporaryDirectory() as temp_dir:
            hook_name = "test_hook"
            
            # Create a mock ps1 and sh script
            ps1_path = os.path.join(temp_dir, f"{hook_name}.ps1")
            sh_path = os.path.join(temp_dir, f"{hook_name}.sh")
            
            with open(ps1_path, "w") as f:
                f.write("echo 'Windows hook'")
            with open(sh_path, "w") as f:
                f.write("echo 'Unix hook'")
                
            original_system = shell_module.platform.system
            original_execute = Shell.execute
            mock_execute = MagicMock(return_value=MagicMock(returncode=0))
            try:
                # Test Windows
                shell_module.platform.system = lambda: "Windows"
                Shell.execute = mock_execute
                
                res = Shell.run_hook(hook_name, temp_dir)
                mock_execute.assert_called_once()
                self.assertIn("powershell", mock_execute.call_args[0][0])
                
                mock_execute.reset_mock()
                
                # Test Unix
                shell_module.platform.system = lambda: "Linux"
                res = Shell.run_hook(hook_name, temp_dir)
                mock_execute.assert_called_once()
                self.assertIn("bash", mock_execute.call_args[0][0])
            finally:
                shell_module.platform.system = original_system
                Shell.execute = original_execute

if __name__ == '__main__':
    unittest.main()
