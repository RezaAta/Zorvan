"""
Search Controller - handles node search functionality.

Extracted from main_window.py to reduce complexity and improve maintainability.
This controller manages finding and highlighting nodes by name.
"""

from PyQt6.QtGui import QColor


class SearchController:
    """Controller for node search operations.

    Manages searching for nodes by name and navigating through results.
    """

    def __init__(self, main_window):
        """Initialize the search controller.

        Args:
            main_window: Reference to the MainWindow instance
        """
        self.main_window = main_window
        self.search_results = []
        self.search_index = -1

    @property
    def canvas(self):
        """Access the canvas from main window."""
        return self.main_window.canvas

    @property
    def status_bar(self):
        """Access the status bar from main window."""
        return self.main_window.status_bar

    @property
    def search_box(self):
        """Access the search box from main window."""
        return self.main_window.search_box

    def highlight_matching_nodes(self):
        """Highlight all nodes matching the search text."""
        search_text = self.search_box.text().strip().lower()

        if not search_text:
            self._clear_highlights()
            return

        # Dim all nodes first
        for node_item in self.canvas.node_items.values():
            node_item.setOpacity(0.3)

        # Find and highlight matching nodes
        self.search_results = []
        for node_item in self.canvas.node_items.values():
            if search_text in node_item.node.name.lower():
                node_item.setOpacity(1.0)
                # Add yellow highlight
                pen = node_item.pen()
                pen.setWidth(4)
                pen.setColor(QColor(255, 255, 0))
                node_item.setPen(pen)
                self.search_results.append(node_item)

        self.search_index = -1

        # Update status
        if self.search_results:
            self.status_bar.showMessage(
                f"Found {len(self.search_results)} node(s) matching '{search_text}'"
            )
        else:
            self.status_bar.showMessage(f"No nodes found matching '{search_text}'")

    def find_node(self):
        """Find and zoom to the first matching node."""
        if self.search_results:
            self.search_index = 0
            self._focus_on_search_result()

    def find_next_node(self):
        """Find and zoom to the next matching node."""
        if not self.search_results:
            self.status_bar.showMessage(
                "No search results. Enter text in the search box."
            )
            return

        self.search_index = (self.search_index + 1) % len(self.search_results)
        self._focus_on_search_result()

    def _clear_highlights(self):
        """Clear all search highlights."""
        for node_item in self.canvas.node_items.values():
            node_item.setOpacity(1.0)
            pen = node_item.pen()
            pen.setWidth(2)
            pen.setColor(QColor(100, 100, 100))
            node_item.setPen(pen)
        self.search_results = []
        self.search_index = -1

    def _focus_on_search_result(self):
        """Focus on the current search result."""
        if not self.search_results or self.search_index < 0:
            return

        node_item = self.search_results[self.search_index]

        # Update all highlights - yellow for matches
        for item in self.search_results:
            pen = item.pen()
            pen.setWidth(4)
            pen.setColor(QColor(255, 255, 0))
            item.setPen(pen)

        # Highlight current with green
        pen = node_item.pen()
        pen.setWidth(6)
        pen.setColor(QColor(0, 255, 0))
        node_item.setPen(pen)

        # Center view on node
        self.canvas.centerOn(node_item)

        # Update status
        self.status_bar.showMessage(
            f"Node {self.search_index + 1} of {len(self.search_results)}: {node_item.node.name}"
        )
