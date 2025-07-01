"""
Main divination module - Initializes and provides access to all divination systems
"""

from logic.base import DivinationRegistry, DivinationType
from logic.iching_adapter import IChingSystem

# Initialize and register all divination systems
def initialize_systems():
    """Initialize and register all available divination systems"""
    # Register I Ching system
    iching_system = IChingSystem()
    DivinationRegistry.register(iching_system)

    print(f"Registered divination systems: {list(DivinationRegistry.get_all_systems().keys())}")

# Initialize systems when module is imported
initialize_systems()

# Convenience functions for common operations
def create_reading(divination_type: DivinationType = DivinationType.ICHING):
    """Create a new reading for the specified divination type"""
    system = DivinationRegistry.get_system(divination_type)
    if system:
        return system.create_reading()
    raise ValueError(f"Unsupported divination type: {divination_type}")

def get_system(divination_type: DivinationType):
    """Get a divination system by type"""
    return DivinationRegistry.get_system(divination_type)

def get_all_systems():
    """Get all registered divination systems"""
    return DivinationRegistry.get_all_systems()

def is_supported(divination_type: DivinationType) -> bool:
    """Check if divination type is supported"""
    return DivinationRegistry.is_supported(divination_type)
