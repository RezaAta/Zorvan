"""
Test script to demonstrate the theme system integration.

This script shows how the new ThemeViewModel works with the ThemeAdapter
to provide theme management capabilities.
"""

import sys

def test_theme_system():
    """Test the theme system components."""
    print("=" * 70)
    print("Theme System Integration Test")
    print("=" * 70)
    print()
    
    # Test 1: ThemeViewModel basic functionality
    print("Test 1: ThemeViewModel Basic Functionality")
    print("-" * 70)
    from gui_framework.viewmodels.theme_viewmodel import ThemeViewModel
    
    vm = ThemeViewModel()
    vm.initialize()
    
    print(f"✓ ThemeViewModel initialized")
    print(f"  Current theme: {vm.current_theme}")
    print(f"  Number of colors: {len(vm.colors)}")
    print(f"  Number of fonts: {len(vm.fonts)}")
    print()
    
    # Test color operations
    print("  Testing color operations:")
    bg_color = vm.get_color("bg")
    print(f"    Background color: {bg_color}")
    
    vm.set_color("accent", "#FF5733")
    new_accent = vm.get_color("accent")
    print(f"    Changed accent to: {new_accent}")
    assert new_accent == "#FF5733", "Color change failed"
    print("  ✓ Color operations working")
    print()
    
    # Test font operations
    print("  Testing font operations:")
    ui_font = vm.get_font("ui")
    print(f"    UI font: {ui_font['family']} {ui_font['size']}pt {ui_font['weight']}")
    
    vm.set_font("node", "Arial", "14", "Bold")
    node_font = vm.get_font("node")
    print(f"    Changed node font to: {node_font['family']} {node_font['size']}pt {node_font['weight']}")
    assert node_font["family"] == "Arial", "Font change failed"
    print("  ✓ Font operations working")
    print()
    
    # Test reset
    print("  Testing reset to defaults:")
    vm.reset_to_defaults()
    reset_accent = vm.get_color("accent")
    print(f"    Accent after reset: {reset_accent}")
    assert reset_accent == "#4a86e8", "Reset failed"
    print("  ✓ Reset to defaults working")
    print()
    
    vm.cleanup()
    print("✓ Test 1 PASSED")
    print()
    
    # Test 2: ThemeMixin functionality
    print("Test 2: ThemeMixin Functionality")
    print("-" * 70)
    from gui_framework.widgets.theme_mixin import ThemeMixin
    
    class TestWidget(ThemeMixin):
        def __init__(self, use_state_store=False):
            self.apply_count = 0
            ThemeMixin.__init__(self, use_state_store=use_state_store)
        
        def apply_theme(self):
            self.apply_count += 1
    
    # Test legacy mode
    print("  Testing legacy mode:")
    widget_legacy = TestWidget(use_state_store=False)
    print(f"    Has theme_manager: {widget_legacy.theme_manager is not None}")
    print(f"    Has theme_viewmodel: {widget_legacy.theme_viewmodel is not None}")
    print(f"    Apply theme called: {widget_legacy.apply_count} times")
    assert widget_legacy.theme_manager is not None, "Legacy mode failed"
    assert widget_legacy.theme_viewmodel is None, "Legacy mode should not have viewmodel"
    print("  ✓ Legacy mode working")
    print()
    
    # Test StateStore mode
    print("  Testing StateStore mode:")
    widget_new = TestWidget(use_state_store=True)
    print(f"    Has theme_manager: {widget_new.theme_manager is not None}")
    print(f"    Has theme_viewmodel: {widget_new.theme_viewmodel is not None}")
    print(f"    Apply theme called: {widget_new.apply_count} times")
    assert widget_new.theme_viewmodel is not None, "StateStore mode failed"
    print("  ✓ StateStore mode working")
    print()
    
    widget_legacy.disconnect_theme()
    widget_new.disconnect_theme()
    print("✓ Test 2 PASSED")
    print()
    
    # Test 3: Observable properties
    print("Test 3: Observable Properties")
    print("-" * 70)
    vm2 = ThemeViewModel()
    vm2.initialize()
    
    observations = []
    vm2.observe_property("colors", lambda old, new: observations.append(new))
    
    vm2.set_color("text", "#FFFFFF")
    print(f"  Property observer called: {len(observations)} times")
    assert len(observations) == 1, "Property observation failed"
    print("  ✓ Observable properties working")
    print()
    
    vm2.cleanup()
    print("✓ Test 3 PASSED")
    print()
    
    # Test 4: Event bus integration
    print("Test 4: Event Bus Integration")
    print("-" * 70)
    from gui_framework.events.bus import get_event_bus, EventType
    
    vm3 = ThemeViewModel()
    vm3.initialize()
    
    events_received = []
    event_bus = get_event_bus()
    event_bus.subscribe(EventType.THEME_COLOR_CHANGED, lambda e: events_received.append(e))
    
    vm3.set_color("border", "#AABBCC")
    print(f"  Events received: {len(events_received)}")
    assert len(events_received) == 1, "Event publishing failed"
    assert events_received[0].payload["color_changed"] == "border", "Event payload incorrect"
    print("  ✓ Event bus integration working")
    print()
    
    vm3.cleanup()
    print("✓ Test 4 PASSED")
    print()
    
    # Summary
    print("=" * 70)
    print("All Tests PASSED! ✓")
    print("=" * 70)
    print()
    print("Theme System Summary:")
    print(f"  - ThemeViewModel: Provides pure Python theme management")
    print(f"  - ThemeMixin: Dual-mode widget integration (legacy + new)")
    print(f"  - Observable properties: Automatic UI updates")
    print(f"  - Event bus: Decoupled communication")
    print(f"  - State store: Centralized state management")
    print()
    return True


if __name__ == "__main__":
    try:
        success = test_theme_system()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
