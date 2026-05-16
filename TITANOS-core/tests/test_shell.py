import unittest
from unittest.mock import patch, MagicMock
import subprocess
import os
import tempfile
from titanos.platform.shell import Shell

class TestShell(unittest.TestCase):
    @patch('titanos.platform.shell.platform.system')
    @patch('titanos.platform.shell.Shell.has_command')
    def test_get_default_shell_windows(self, mock_has_command, mock_system):
        mock_system.return_value = "Windows"
        
        # Test pwsh preference
        mock_has_command.side_effect = lambda cmd: cmd == "pwsh"
        self.assertEqual(Shell.get_default_shell(), "pwsh")

        mock_has_command.side_effect = lambda cmd: cmd == "powershell"
        self.assertEqual(Shell.get_default_shell(), "powershell")

        mock_has_command.side_effect = lambda cmd: False
        self.assertEqual(Shell.get_default_shell(), "cmd")

    @patch('titanos.platform.shell.platform.system')
    @patch('titanos.platform.shell.Shell.has_command')
    def test_get_default_shell_unix(self, mock_has_command, mock_system):
        mock_system.return_value = "Linux"
        
        # Test bash preference
        mock_has_command.side_effect = lambda cmd: cmd == "bash"
        self.assertEqual(Shell.get_default_shell(), "bash")
        
        # Test fallback
        mock_has_command.side_effect = lambda cmd: False
        self.assertEqual(Shell.get_default_shell(), "sh")

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
                
            with patch('titanos.platform.shell.platform.system') as mock_system, patch('titanos.platform.shell.Shell.execute') as mock_execute:
                # Test Windows
                mock_system.return_value = "Windows"
                mock_execute.return_value = MagicMock(returncode=0)
                
                res = Shell.run_hook(hook_name, temp_dir)
                mock_execute.assert_called_once()
                self.assertIn("powershell", mock_execute.call_args[0][0])
                
                mock_execute.reset_mock()
                
                # Test Unix
                mock_system.return_value = "Linux"
                res = Shell.run_hook(hook_name, temp_dir)
                mock_execute.assert_called_once()
                self.assertIn("bash", mock_execute.call_args[0][0])

if __name__ == '__main__':
    unittest.main()
