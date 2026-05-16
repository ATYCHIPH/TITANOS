import unittest
import logging
import json
from titanos.platform.logging import JSONFormatter, setup_logging

class TestLogging(unittest.TestCase):
    def test_json_formatter(self):
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="This is a test message",
            args=(),
            exc_info=None,
            func="test_func",
            sinfo=None
        )
        
        formatted = formatter.format(record)
        data = json.loads(formatted)
        
        self.assertEqual(data["name"], "test_logger")
        self.assertEqual(data["level"], "INFO")
        self.assertEqual(data["message"], "This is a test message")
        self.assertIn("timestamp", data)
        self.assertNotIn("exception", data)

    def test_json_formatter_exception(self):
        formatter = JSONFormatter()
        
        try:
            1 / 0
        except Exception as e:
            import sys
            exc_info = sys.exc_info()
            
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="An error occurred",
            args=(),
            exc_info=exc_info,
            func="test_func",
            sinfo=None
        )
        
        formatted = formatter.format(record)
        data = json.loads(formatted)
        
        self.assertEqual(data["level"], "ERROR")
        self.assertEqual(data["message"], "An error occurred")
        self.assertIn("exception", data)
        self.assertIn("ZeroDivisionError", data["exception"])

    def test_setup_logging(self):
        # Just ensure it doesn't crash and sets up handlers
        setup_logging(json_format=True)
        root_logger = logging.getLogger()
        self.assertTrue(any(isinstance(h.formatter, JSONFormatter) for h in root_logger.handlers))

if __name__ == '__main__':
    unittest.main()
