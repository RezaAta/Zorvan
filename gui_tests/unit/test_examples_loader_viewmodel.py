from gui_framework.viewmodels.examples_loader_viewmodel import ExamplesLoaderViewModel


def test_examples_list_returns_items():
    vm = ExamplesLoaderViewModel()
    examples = vm.list_examples()
    # Should at least find one example in the repository
    assert isinstance(examples, dict)
    assert len(examples) > 0
    # Each entry should be (path, desc)
    for k, (p, d) in examples.items():
        assert isinstance(k, str)
        assert isinstance(p, str)
        assert isinstance(d, str)
        break
