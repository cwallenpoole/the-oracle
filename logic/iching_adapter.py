"""
I Ching Adapter - Bridges the existing I Ching system with the new base classes
"""

from typing import Optional, List, Dict, Any
from logic.base import DivinationReading, DivinationSystem, DivinationElement, DivinationType
from logic import iching


class IChingElement(DivinationElement):
    """Wrapper for I Ching hexagrams to fit the new system"""

    def __init__(self, hexagram: iching.IChingHexagram):
        self.hexagram = hexagram
        super().__init__(
            identifier=str(hexagram.Number),
            name=hexagram.Title,
            symbol=hexagram.Symbol,
            description=hexagram.About.Description,
            metadata={
                'above': hexagram.About.Above,
                'below': hexagram.About.Below,
                'judgement': hexagram.Judgement,
                'image': hexagram.Image,
                'lines': hexagram.Lines,
                'content': hexagram.Content
            }
        )


class IChingReading(DivinationReading):
    """Wrapper for I Ching readings to fit the new system"""

    def __init__(self, reading: Optional[iching.Reading] = None):
        super().__init__(DivinationType.ICHING)
        self._legacy_reading = reading
        if reading:
            self._populate_from_legacy(reading)

    def _populate_from_legacy(self, reading: iching.Reading):
        """Populate from legacy Reading object"""
        if reading.Current:
            self.elements.append(IChingElement(reading.Current))

        if reading.Future:
            self.elements.append(IChingElement(reading.Future))
            self.has_transformation = True

    def cast(self) -> None:
        """Perform I Ching casting"""
        self._legacy_reading = iching.cast_hexagrams()
        self.elements.clear()
        self._populate_from_legacy(self._legacy_reading)

    def get_primary_element(self) -> DivinationElement:
        """Get the current/primary hexagram"""
        return self.elements[0] if self.elements else None

    def get_secondary_element(self) -> Optional[DivinationElement]:
        """Get the future/secondary hexagram"""
        return self.elements[1] if len(self.elements) > 1 else None

    def to_string(self) -> str:
        """Convert to string representation"""
        if self._legacy_reading:
            return str(self._legacy_reading)
        return ""

    def get_display_data(self) -> Dict[str, Any]:
        """Get data formatted for display"""
        data = {
            'type': 'iching',
            'primary': None,
            'secondary': None,
            'has_transition': self.has_transformation
        }

        if self.elements:
            primary = self.elements[0]
            data['primary'] = {
                'number': int(primary.identifier),
                'title': primary.name,
                'symbol': primary.symbol,
                'description': primary.description,
                'hexagram': primary.hexagram if hasattr(primary, 'hexagram') else None
            }

            if len(self.elements) > 1:
                secondary = self.elements[1]
                data['secondary'] = {
                    'number': int(secondary.identifier),
                    'title': secondary.name,
                    'symbol': secondary.symbol,
                    'description': secondary.description,
                    'hexagram': secondary.hexagram if hasattr(secondary, 'hexagram') else None
                }

        return data

    @property
    def Current(self):
        """Legacy compatibility property"""
        return self._legacy_reading.Current if self._legacy_reading else None

    @property
    def Future(self):
        """Legacy compatibility property"""
        return self._legacy_reading.Future if self._legacy_reading else None


class IChingSystem(DivinationSystem):
    """I Ching divination system"""

    def __init__(self):
        super().__init__(DivinationType.ICHING)
        self._elements_cache = None

    def create_reading(self) -> IChingReading:
        """Create a new I Ching reading"""
        reading = IChingReading()
        reading.cast()
        return reading

    def get_element_by_identifier(self, identifier: str) -> Optional[IChingElement]:
        """Get hexagram by number"""
        try:
            number = int(identifier)
            if 1 <= number <= 64:
                hexagram = iching.get_hexagram_section(number)
                return IChingElement(hexagram) if hexagram else None
        except ValueError:
            pass
        return None

    def get_all_elements(self) -> List[IChingElement]:
        """Get all 64 hexagrams"""
        if self._elements_cache is None:
            self._elements_cache = []
            for i in range(1, 65):
                hexagram = iching.get_hexagram_section(i)
                if hexagram:
                    self._elements_cache.append(IChingElement(hexagram))
        return self._elements_cache

    def get_system_name(self) -> str:
        """Get system name"""
        return "I Ching"

    def get_system_description(self) -> str:
        """Get system description"""
        return "The ancient Chinese Book of Changes, offering wisdom through 64 hexagrams"


def create_iching_reading_from_legacy(legacy_reading: iching.Reading) -> IChingReading:
    """Create new-style reading from legacy reading object"""
    return IChingReading(legacy_reading)


def get_legacy_reading_from_iching(iching_reading: IChingReading) -> iching.Reading:
    """Extract legacy reading object from new-style reading"""
    return iching_reading._legacy_reading
