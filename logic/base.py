from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class DivinationType(Enum):
    """Supported divination types"""
    ICHING = "iching"
    RUNES = "runes"
    TAROT = "tarot"


@dataclass
class DivinationElement:
    """Base class for individual divination elements (hexagrams, runes, cards)"""
    identifier: str  # Unique identifier (number, name, etc.)
    name: str
    symbol: str
    description: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DivinationReading(ABC):
    """Abstract base class for all divination readings"""

    def __init__(self, divination_type: DivinationType):
        self.divination_type = divination_type
        self.elements: List[DivinationElement] = []
        self.has_transformation = False
        self.metadata: Dict[str, Any] = {}

    @abstractmethod
    def cast(self) -> None:
        """Perform the divination casting"""
        pass

    @abstractmethod
    def get_primary_element(self) -> DivinationElement:
        """Get the main/primary element of the reading"""
        pass

    @abstractmethod
    def get_secondary_element(self) -> Optional[DivinationElement]:
        """Get the secondary/future element if it exists"""
        pass

    @abstractmethod
    def to_string(self) -> str:
        """Convert reading to string representation"""
        pass

    @abstractmethod
    def get_display_data(self) -> Dict[str, Any]:
        """Get data formatted for display in templates"""
        pass

    def has_transition(self) -> bool:
        """Check if reading has a transformation/transition"""
        return self.has_transformation

    def __str__(self) -> str:
        return self.to_string()


class DivinationSystem(ABC):
    """Abstract base class for divination systems"""

    def __init__(self, divination_type: DivinationType):
        self.divination_type = divination_type

    @abstractmethod
    def create_reading(self) -> DivinationReading:
        """Create a new reading"""
        pass

    @abstractmethod
    def get_element_by_identifier(self, identifier: str) -> Optional[DivinationElement]:
        """Get a specific element by its identifier"""
        pass

    @abstractmethod
    def get_all_elements(self) -> List[DivinationElement]:
        """Get all elements in this divination system"""
        pass

    @abstractmethod
    def get_system_name(self) -> str:
        """Get the display name of this divination system"""
        pass

    @abstractmethod
    def get_system_description(self) -> str:
        """Get a description of this divination system"""
        pass


class DivinationRegistry:
    """Registry for all available divination systems"""

    _systems: Dict[DivinationType, DivinationSystem] = {}

    @classmethod
    def register(cls, system: DivinationSystem) -> None:
        """Register a divination system"""
        cls._systems[system.divination_type] = system

    @classmethod
    def get_system(cls, divination_type: DivinationType) -> Optional[DivinationSystem]:
        """Get a registered divination system"""
        return cls._systems.get(divination_type)

    @classmethod
    def get_all_systems(cls) -> Dict[DivinationType, DivinationSystem]:
        """Get all registered systems"""
        return cls._systems.copy()

    @classmethod
    def is_supported(cls, divination_type: DivinationType) -> bool:
        """Check if a divination type is supported"""
        return divination_type in cls._systems


# Utility functions for working with readings
def parse_reading_from_string(reading_string: str, divination_type: DivinationType) -> Optional[DivinationReading]:
    """Parse a reading from its string representation"""
    system = DivinationRegistry.get_system(divination_type)
    if not system:
        return None

    # This would need to be implemented by each system
    # For now, return None - we'll implement this when we refactor I Ching
    return None


def enhance_reading_text_with_links(reading_text: str, divination_type: DivinationType) -> str:
    """Enhance reading text with links to relevant elements"""
    # This will be implemented based on the specific divination type
    # For now, return the original text
    return reading_text
