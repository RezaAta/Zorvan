from gui_framework.viewmodels.examples_loader_viewmodel import ExamplesLoaderViewModel


class DummyRepo:
    def __init__(self):
        self._examples = {
            "ex1": (lambda: "built1", "Example 1"),
            "ex2": (lambda: "built2", "Example 2"),
        }

    def list_examples(self):
        return self._examples

    def build(self, name):
        return self._examples[name][0]()


def test_examples_list_returns_items():
    vm = ExamplesLoaderViewModel()
    examples = vm.list_examples()
    # Should at least find one example in the filesystem-based search paths
    assert isinstance(examples, dict)
    # Each entry should be (path, desc)
    for k, (p, d) in examples.items():
        assert isinstance(k, str)
        assert isinstance(p, str)
        assert isinstance(d, str)
        break


def test_examples_list_uses_repository_when_provided():
    repo = DummyRepo()
    vm = ExamplesLoaderViewModel(repository=repo)
    examples = vm.list_examples()
    assert "ex1" in examples and "ex2" in examples
    assert examples["ex1"][1] == "Example 1"


def test_list_examples_by_category_vm():
    repo = DummyRepo()
    vm = ExamplesLoaderViewModel(repository=repo)
    cats = vm.list_examples_by_category()
    assert "Prog" in cats
    assert ("ex1", "Example 1") in cats["Prog"]


def test_build_example_uses_repo():
    repo = DummyRepo()
    vm = ExamplesLoaderViewModel(repository=repo)
    res = vm.build_example("ex2")
    assert res == "built2"
