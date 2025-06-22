"""Tests for example model functionality."""

import unittest

from model.example_model import ExampleModel


class TestExampleModel(unittest.TestCase):
    """Test cases for ExampleModel."""

    def test_example_model(self) -> None:




        """Test basic ExampleModel functionality."""
        model = ExampleModel("test")
        assert model.name == "test"


if __name__ == "__main__":
    unittest.main()
