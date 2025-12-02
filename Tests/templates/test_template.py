import pytest

# Template for tests in this project. Follow this skeleton for new tests.


# 1. Setup fixtures if necessary
@pytest.fixture
def sample_data():
    return {"a": 1, "b": 2}


# 2. Write a failing test demonstrating desired behavior first
def test_sample_behavior(sample_data):
    # This is an example test - replace with your behavior test
    assert sample_data["a"] + sample_data["b"] == 3


# 3. Add more tests for edge cases, negative cases, and boundaries
def test_sample_negative(sample_data):
    assert sample_data["a"] - sample_data["b"] == -1
