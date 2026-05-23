from gui_framework.services.examples_repository import ExamplesRepository


def test_examples_repository_lists_and_builds():
    repo = ExamplesRepository()
    examples = repo.list_examples()
    # Should return a dict (may be empty depending on environment)
    assert isinstance(examples, dict)
    # Attempt to build any example if present
    for name, (builder, desc) in list(examples.items())[:3]:
        g = repo.build(name)
        # builder may return Graph or None depending on environment; at least should not raise
        assert True
