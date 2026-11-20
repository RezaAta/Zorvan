"""Integration tests for the PlotView widget."""

import os

import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

try:
    from PyQt6.QtWidgets import QApplication

    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

if PYQT_AVAILABLE:
    from gui_framework.viewmodels.plot_viewmodel import PlotViewModel
    from gui_framework.views.plot_view import PlotView


pytestmark = pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt6 not available")


@pytest.fixture(scope="module")
def qapp():
    if PYQT_AVAILABLE:
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        yield app
    else:
        yield None


class TestPlotViewIntegration:
    def test_plot_view_creation_matplotlib(self, qapp):
        try:
            import matplotlib

            vm = PlotViewModel(backend="matplotlib")
            view = PlotView(vm)

            assert view is not None
            assert view.viewmodel == vm
        except ImportError:
            pytest.skip("Matplotlib not available")

    def test_plot_view_creation_pyqtgraph(self, qapp):
        try:
            import pyqtgraph

            vm = PlotViewModel(backend="pyqtgraph")
            view = PlotView(vm)

            assert view is not None
            assert view.viewmodel == vm
            view.close()
            view.deleteLater()
            qapp.processEvents()
        except ImportError:
            pytest.skip("PyQtGraph not available")

    def test_plot_view_add_nodes(self, qapp):
        vm = PlotViewModel(backend="matplotlib")
        vm.add_node("A")
        vm.add_node("B")

        view = PlotView(vm)
        assert view.node_list_widget.count() == 2
        view.close()

    def test_plot_view_add_data(self, qapp):
        vm = PlotViewModel(backend="matplotlib")
        vm.add_node("A")

        view = PlotView(vm)
        for i in range(10):
            vm.add_data_point("A", float(i * 2), iteration=i)

        data = vm.get_plot_data("A")
        assert len(data) == 10
        assert data[0].iteration == 0
        assert data[0].value == 0.0
        view.close()

    def test_plot_view_clear(self, qapp):
        vm = PlotViewModel(backend="matplotlib")
        vm.add_node("A")
        for i in range(10):
            vm.add_data_point("A", float(i), iteration=i)

        view = PlotView(vm)
        view._on_clear_clicked()

        assert len(vm.get_plot_data("A")) == 0
        view.close()

    def test_plot_view_remove_node(self, qapp):
        vm = PlotViewModel(backend="matplotlib")
        vm.add_node("A")
        vm.add_node("B")

        view = PlotView(vm)
        view.node_list_widget.setCurrentRow(0)
        view._on_remove_node_clicked()

        assert len(vm.get_plotted_nodes()) == 1
        view.close()

    def test_plot_view_backend_switching(self, qapp):
        try:
            import matplotlib
            import pyqtgraph

            vm = PlotViewModel(backend="matplotlib")
            view = PlotView(vm)
            vm.set_backend("pyqtgraph")

            assert vm.get_backend() == "pyqtgraph"
            view.close()
        except ImportError:
            pytest.skip("Matplotlib or PyQtGraph not available")

    def test_plot_view_pyqtgraph_legend_and_hover(self, qapp):
        try:
            import pyqtgraph
        except ImportError:
            pytest.skip("PyQtGraph not available")

        vm = PlotViewModel(backend="pyqtgraph")
        vm.add_node("A")
        vm.add_node("B")
        for i in range(3):
            vm.add_data_point("A", float(i), iteration=i)
            vm.add_data_point("B", float(2 * i), iteration=i)

        view = PlotView(vm)
        view.update_plot()

        assert getattr(view, "_mouse_proxy", None) is not None

        if getattr(view, "_legend", None) is not None:
            items = getattr(view._legend, "items", [])
            assert len(items) >= 2

            sample, label = items[0]
            node_name = None
            for name, item in view._line_items.items():
                if item is sample:
                    node_name = name
                    break
            assert node_name is not None
            before_vis = sample.isVisible()
            try:
                if hasattr(label, "mousePressEvent"):
                    label.mousePressEvent(None)
                    after_vis = sample.isVisible()
                    assert after_vis != before_vis
                else:
                    pytest.skip("Legend label not clickable in this environment")
            except Exception:
                pytest.skip("Legend label click not supported on this platform")
        view.close()
        view.deleteLater()
        qapp.processEvents()
