"""
Custom Node Manager for creating, saving, loading, and managing user-defined nodes.

This module provides:
- CustomNodeDefinition: Dataclass storing node configuration and operation code
- CustomNodeManager: Registry for custom nodes with save/load and dynamic class generation
"""

import json
import os
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Type

import numpy as np

from ComputationalGraphs.Nodes.BasicNode import BasicNode


@dataclass
class CustomNodeDefinition:
    """Definition of a user-created custom node.

    Attributes:
        type_name: The class/type name for the node (e.g., "MyCustomNode")
        input_count: Number of inputs the node expects
        batch_size: Batch processing size
        inclusive: Whether node's result is added to next batch
        forced_batch_processing: Continue processing until insufficient inputs
        valid_input_types: List of valid input types ("numeric", "string", "array", "none")
        operation_code: Python code for the Operation body (uses input1, input2, etc.)
        description: Optional description for display in palette
        custom_properties: List of custom property definitions,
            each with name, type, default_value
    """

    type_name: str
    input_count: int = 2
    batch_size: int = 2
    inclusive: bool = True
    forced_batch_processing: bool = False
    valid_input_types: List[str] = field(default_factory=lambda: ["numeric"])
    operation_code: str = "return input1 + input2"
    description: str = ""
    custom_properties: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CustomNodeDefinition":
        """Create from dictionary (JSON deserialization)."""
        return cls(**data)

    def validate_operation_code(self) -> Optional[str]:
        """Validate the operation code syntax.

        Returns:
            None if valid, error message string if invalid.
        """
        # Build the full function code to compile
        input_params = ", ".join(f"input{i+1}" for i in range(self.input_count))
        full_code = f"def _test_operation(self, {input_params}):\n"
        # Indent each line of operation code
        for line in self.operation_code.split("\n"):
            full_code += f"    {line}\n"

        try:
            compile(full_code, "<custom_node>", "exec")
            return None
        except SyntaxError as e:
            return f"Syntax error at line {e.lineno}: {e.msg}"


class CustomNodeManager:
    """Manager for custom node definitions.

    Handles:
    - Registry of custom node definitions
    - Save/load to JSON library file
    - Dynamic class generation from definitions
    - Integration with node factory
    """

    # Default library filename
    DEFAULT_LIBRARY_FILE = "custom_nodes.json"

    def __init__(self, library_path: Optional[str] = None):
        """Initialize the manager.

        Args:
            library_path: Path to the custom nodes library file.
                         If None, uses default in current directory.
        """
        self.library_path = library_path or self.DEFAULT_LIBRARY_FILE
        self._definitions: Dict[str, CustomNodeDefinition] = {}
        self._generated_classes: Dict[str, Type] = {}

    @property
    def definitions(self) -> Dict[str, CustomNodeDefinition]:
        """Get all registered custom node definitions."""
        return self._definitions.copy()

    def get_definition(self, type_name: str) -> Optional[CustomNodeDefinition]:
        """Get a specific definition by type name."""
        return self._definitions.get(type_name)

    def add_definition(self, definition: CustomNodeDefinition) -> bool:
        """Add or update a custom node definition.

        Args:
            definition: The node definition to add

        Returns:
            True if added successfully
        """
        # Validate operation code
        error = definition.validate_operation_code()
        if error:
            raise ValueError(f"Invalid operation code: {error}")

        # Prevent overriding built-in node types
        try:
            from . import node_factory

            if node_factory.is_builtin_node(definition.type_name):
                raise ValueError(
                    "Cannot create custom node using built-in name '"
                    + definition.type_name
                    + "'."
                )
        except Exception:
            # If node_factory not available, be conservative and continue
            pass

        self._definitions[definition.type_name] = definition
        # Regenerate class
        self._generate_class(definition)
        return True

    def remove_definition(self, type_name: str) -> bool:
        """Remove a custom node definition.

        Args:
            type_name: The type name to remove

        Returns:
            True if removed, False if not found
        """
        if type_name in self._definitions:
            del self._definitions[type_name]
            if type_name in self._generated_classes:
                del self._generated_classes[type_name]
            # Unregister from factory if available
            try:
                from . import node_factory

                node_factory.unregister_node_type(type_name)
            except Exception:
                pass
            return True
        return False

    def get_node_class(self, type_name: str) -> Optional[Type]:
        """Get the dynamically generated class for a custom node type.

        Args:
            type_name: The type name of the custom node

        Returns:
            The generated class, or None if not found
        """
        if type_name not in self._generated_classes:
            if type_name in self._definitions:
                self._generate_class(self._definitions[type_name])
        return self._generated_classes.get(type_name)

    def _generate_class(self, definition: CustomNodeDefinition) -> Type:
        """Generate a dynamic class from a node definition.

        Args:
            definition: The node definition

        Returns:
            The generated class
        """
        # Build input parameters string
        input_params = ", ".join(f"input{i+1}" for i in range(definition.input_count))

        # Build IsValidInput check based on valid_input_types
        valid_checks = []
        if "numeric" in definition.valid_input_types:
            valid_checks.append(
                "isinstance(inp, (int, float, np.integer, np.floating))"
            )
        if "string" in definition.valid_input_types:
            valid_checks.append("isinstance(inp, str)")
        if "array" in definition.valid_input_types:
            valid_checks.append("isinstance(inp, (list, tuple, np.ndarray))")
        if "none" in definition.valid_input_types:
            valid_checks.append("inp is None")

        if valid_checks:
            valid_check_code = " or ".join(valid_checks)
        else:
            valid_check_code = "True"  # Accept anything if no types specified

        # Build custom properties initialization code
        custom_props_init = ""
        for prop in definition.custom_properties:
            prop_name = prop.get("name", "")
            prop_default = prop.get("default_value", "None")
            if prop_name:
                # Safely quote strings, leave other values as-is
                custom_props_init += f"        self.{prop_name} = {prop_default}\n"

        # Build the class code
        class_code = f'''
class {definition.type_name}(BasicNode):
    """Custom node: {definition.description or definition.type_name}"""

    # Mark as custom node for serialization
    _is_custom_node = True
    _custom_definition_dict = {repr(definition.to_dict())}

    def __init__(self, name: str = "", value=0):
        super().__init__(name, value)
        self.inputCount = {definition.input_count}
        self.batchSize = {definition.batch_size}
        self.inclusive = {definition.inclusive}
        self.forcedBatchProcessing = {definition.forced_batch_processing}
{custom_props_init}
    def Operation(self, {input_params}):
{self._indent_code(definition.operation_code, 8)}

    def IsValidInput(self, inp):
        return {valid_check_code}
'''

        # Execute to create the class
        namespace = {
            "BasicNode": BasicNode,
            "np": np,
        }

        try:
            exec(class_code, namespace)
            cls = namespace[definition.type_name]
            self._generated_classes[definition.type_name] = cls
            return cls
        except Exception as e:
            raise ValueError(
                f"Failed to generate class for {definition.type_name}: {e}"
            )

    def _indent_code(self, code: str, spaces: int) -> str:
        """Indent code by specified number of spaces."""
        indent = " " * spaces
        lines = code.split("\n")
        return "\n".join(indent + line for line in lines)

    def save_library(self, path: Optional[str] = None) -> bool:
        """Save all definitions to the library file.

        Args:
            path: Optional path override

        Returns:
            True if saved successfully
        """
        save_path = path or self.library_path

        data = {
            "version": 1,
            "custom_nodes": [d.to_dict() for d in self._definitions.values()],
        }

        try:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            import logging

            logging.getLogger(__name__).warning(
                "Failed to save custom nodes library: %s", e
            )
            return False

    def load_library(self, path: Optional[str] = None) -> bool:
        """Load definitions from the library file.

        Args:
            path: Optional path override

        Returns:
            True if loaded successfully (or file doesn't exist)
        """
        load_path = path or self.library_path

        if not os.path.exists(load_path):
            return True  # No library file is OK

        try:
            with open(load_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Clear existing
            self._definitions.clear()
            self._generated_classes.clear()

            # Load definitions
            for node_data in data.get("custom_nodes", []):
                try:
                    definition = CustomNodeDefinition.from_dict(node_data)
                    self._definitions[definition.type_name] = definition
                    self._generate_class(definition)
                except Exception as e:
                    import logging

                    logging.getLogger(__name__).exception(
                        "Failed to load custom node "
                        + str(node_data.get("type_name", "unknown"))
                        + ": "
                        + str(e)
                    )

            return True
        except Exception as e:
            import logging

            logging.getLogger(__name__).warning(
                "Failed to load custom nodes library: %s", e
            )
            return False

    def create_node(self, type_name: str, name: str = "") -> Optional[BasicNode]:
        """Create an instance of a custom node.

        Args:
            type_name: The custom node type name
            name: Instance name for the node

        Returns:
            Node instance, or None if type not found
        """
        cls = self.get_node_class(type_name)
        if cls is None:
            return None

        try:
            return cls(name=name)
        except Exception as e:
            print(f"Failed to create custom node {type_name}: {e}")
            return None

    def get_type_names(self) -> List[str]:
        """Get list of all registered custom node type names."""
        return list(self._definitions.keys())

    def register_with_factory(self):
        """Register all custom nodes with the node factory."""
        from . import node_factory

        for type_name, definition in self._definitions.items():
            # Register using a special module path marker
            node_factory.register_node_type(
                node_type=type_name,
                module_path="__custom__",  # Special marker
                class_name=type_name,
                default_kwargs={},
                name_prefix=type_name.replace("Node", "") or "Custom",
            )

    def unregister_with_factory(self):
        """Unregister all custom nodes from the node factory."""
        try:
            from . import node_factory

            for type_name in list(self._definitions.keys()):
                node_factory.unregister_node_type(type_name)
        except Exception:
            pass


# Global instance for convenience
_global_manager: Optional[CustomNodeManager] = None


def get_custom_node_manager() -> CustomNodeManager:
    """Get the global CustomNodeManager instance."""
    global _global_manager
    if _global_manager is None:
        _global_manager = CustomNodeManager()
        _global_manager.load_library()
    return _global_manager


def set_custom_node_manager(manager: CustomNodeManager):
    """Set the global CustomNodeManager instance."""
    global _global_manager
    _global_manager = manager
