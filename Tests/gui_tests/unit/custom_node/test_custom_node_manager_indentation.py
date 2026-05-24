import pytest

pytest.importorskip("PyQt6")

from gui_framework.legacy import CustomNodeDefinition, CustomNodeManager


def test_operation_code_with_leading_blank_and_tabs_is_valid():
    mgr = CustomNodeManager(library_path=None)
    code = "\n\treturn input1 + input2"
    d = CustomNodeDefinition(type_name="TestNode", input_count=2, operation_code=code)

    # validate should succeed (we normalize dedent)
    err = d.validate_operation_code()
    assert err is None

    # And manager should be able to generate the class
    cls = mgr._generate_class(d)
    assert cls.__name__ == "TestNode"


def test_invalid_operation_shows_snippet():
    mgr = CustomNodeManager(library_path=None)
    code = "return input1 +\n  invalid!!"
    d = CustomNodeDefinition(type_name="BadNode", input_count=1, operation_code=code)

    with pytest.raises(ValueError) as ei:
        mgr._generate_class(d)
    msg = str(ei.value)
    assert "Syntax error" in msg
    assert "BadNode" in msg
    # should include generated code snippet marker '^'
    assert "^" in msg
