import unittest

from llm_endpoint.tools import get_runtime_info


class RuntimeToolTests(unittest.TestCase):
    def test_python_version_is_allowlisted(self) -> None:
        result = get_runtime_info({"field": "python_version"})
        self.assertEqual(result["field"], "python_version")
        self.assertRegex(result["value"], r"^\d+\.\d+")

    def test_unknown_field_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            get_runtime_info({"field": "environment"})


if __name__ == "__main__":
    unittest.main()
