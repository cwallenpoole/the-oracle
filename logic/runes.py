"""
Runic divination system implementation.

This module provides the Elder Futhark runic system for divination,
including rune meanings, casting methods, and reading interpretations.
"""

import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from logic.base import DivinationElement, DivinationReading, DivinationSystem, DivinationType


@dataclass
class RuneElement(DivinationElement):
    """Represents a single rune with its meaning and attributes"""
    phonetic: str = ""
    element: str = ""
    deity: str = ""
    reversed_meaning: str = ""
    is_reversed: bool = False

    def get_display_meaning(self) -> str:
        """Get the appropriate meaning based on orientation"""
        if self.is_reversed and self.reversed_meaning:
            return f"{self.description} (Reversed: {self.reversed_meaning})"
        return self.description

    def __str__(self) -> str:
        orientation = " (Reversed)" if self.is_reversed else ""
        return f"{self.symbol} {self.name}{orientation}: {self.get_display_meaning()}"


class RuneSpread:
    """Defines different runic spread layouts"""

    @staticmethod
    def single_rune() -> Dict[str, str]:
        """Single rune for simple guidance"""
        return {"position_1": "Guidance"}

    @staticmethod
    def three_norns() -> Dict[str, str]:
        """Past, Present, Future spread"""
        return {
            "position_1": "Past (Urd - What was)",
            "position_2": "Present (Verdandi - What is)",
            "position_3": "Future (Skuld - What will be)"
        }

    @staticmethod
    def five_cross() -> Dict[str, str]:
        """Five rune cross spread"""
        return {
            "position_1": "Present Situation",
            "position_2": "Challenge/Problem",
            "position_3": "Past Influence",
            "position_4": "Possible Future",
            "position_5": "Action to Take"
        }

    @staticmethod
    def seven_chakras() -> Dict[str, str]:
        """Seven rune chakra spread"""
        return {
            "position_1": "Root - Foundation/Security",
            "position_2": "Sacral - Creativity/Relationships",
            "position_3": "Solar Plexus - Personal Power",
            "position_4": "Heart - Love/Compassion",
            "position_5": "Throat - Communication/Truth",
            "position_6": "Third Eye - Intuition/Wisdom",
            "position_7": "Crown - Spiritual Connection"
        }


class RunicReading(DivinationReading):
    """Represents a complete runic reading"""

    def __init__(self, runes: List[RuneElement], spread_type: str, spread_positions: Dict[str, str]):
        self.runes = runes
        self.spread_type = spread_type
        self.spread_positions = spread_positions
        super().__init__(DivinationType.RUNES)

    def get_elements(self) -> List[DivinationElement]:
        """Return the runes as divination elements"""
        return self.runes

    def get_primary_element(self) -> DivinationElement:
        """Return the first rune as primary"""
        return self.runes[0] if self.runes else None

    def has_transition(self) -> bool:
        """Runic readings don't have transitions like I Ching"""
        return False

    def get_summary(self) -> str:
        """Get a summary of the reading"""
        if not self.runes:
            return "Empty runic reading"

        if len(self.runes) == 1:
            return f"Single Rune: {self.runes[0].name}"

        rune_names = [rune.name for rune in self.runes]
        return f"{self.spread_type}: {', '.join(rune_names)}"

    def cast(self) -> None:
        """Runic readings are cast when created, no additional casting needed"""
        pass

    def get_secondary_element(self) -> Optional[DivinationElement]:
        """Runic readings don't have secondary elements like I Ching"""
        return None

    def to_string(self) -> str:
        """Convert reading to string representation"""
        return self.__str__()

    def get_display_data(self) -> Dict[str, Any]:
        """Get data formatted for display in templates"""
        return {
            "type": "runic",
            "spread_type": self.spread_type,
            "runes": [
                {
                    "name": rune.name,
                    "symbol": rune.symbol,
                    "meaning": rune.get_display_meaning(),
                    "is_reversed": rune.is_reversed,
                    "element": rune.element,
                    "deity": rune.deity,
                    "phonetic": rune.phonetic
                }
                for rune in self.runes
            ],
            "positions": self.spread_positions
        }

    def __str__(self) -> str:
        """String representation of the reading"""
        if not self.runes:
            return "Empty runic reading"

        result = [f"Runic Reading - {self.spread_type}"]

        for i, rune in enumerate(self.runes, 1):
            position_key = f"position_{i}"
            position_name = self.spread_positions.get(position_key, f"Position {i}")
            orientation = " (Reversed)" if rune.is_reversed else ""
            result.append(f"\n{position_name}: {rune.symbol} {rune.name}{orientation}")
            result.append(f"   {rune.get_display_meaning()}")

        return "".join(result)


class RunicSystem(DivinationSystem):
    """Elder Futhark runic divination system"""

    def __init__(self):
        super().__init__(DivinationType.RUNES)
        self.runes_data = self._get_elder_futhark_runes()

    def _get_elder_futhark_runes(self) -> List[Dict[str, Any]]:
        """Get the 24 Elder Futhark runes with their meanings"""
        return [
            {
                "name": "Fehu", "symbol": "ᚠ", "phonetic": "F",
                "meaning": "Wealth, abundance, prosperity, new beginnings",
                "reversed_meaning": "Loss, financial difficulties, greed",
                "element": "Fire", "deity": "Freyr"
            },
            {
                "name": "Uruz", "symbol": "ᚢ", "phonetic": "U",
                "meaning": "Strength, vitality, determination, primal power",
                "reversed_meaning": "Weakness, missed opportunities, poor health",
                "element": "Earth", "deity": "Thor"
            },
            {
                "name": "Thurisaz", "symbol": "ᚦ", "phonetic": "TH",
                "meaning": "Protection, conflict, breakthrough, Thor's hammer",
                "reversed_meaning": "Danger, betrayal, poor judgment",
                "element": "Fire", "deity": "Thor"
            },
            {
                "name": "Ansuz", "symbol": "ᚨ", "phonetic": "A",
                "meaning": "Communication, wisdom, divine inspiration, Odin's breath",
                "reversed_meaning": "Miscommunication, deception, lack of clarity",
                "element": "Air", "deity": "Odin"
            },
            {
                "name": "Raidho", "symbol": "ᚱ", "phonetic": "R",
                "meaning": "Journey, progress, rhythm, personal development",
                "reversed_meaning": "Delays, stagnation, wrong direction",
                "element": "Air", "deity": "Thor"
            },
            {
                "name": "Kenaz", "symbol": "ᚲ", "phonetic": "K",
                "meaning": "Knowledge, creativity, illumination, controlled fire",
                "reversed_meaning": "Ignorance, lack of creativity, burnout",
                "element": "Fire", "deity": "Loki"
            },
            {
                "name": "Gebo", "symbol": "ᚷ", "phonetic": "G",
                "meaning": "Gift, partnership, balance, generosity",
                "reversed_meaning": "Cannot be reversed - always positive",
                "element": "Air", "deity": "Odin"
            },
            {
                "name": "Wunjo", "symbol": "ᚹ", "phonetic": "W",
                "meaning": "Joy, harmony, fulfillment, shared happiness",
                "reversed_meaning": "Sorrow, alienation, disappointment",
                "element": "Air", "deity": "Frigg"
            },
            {
                "name": "Hagalaz", "symbol": "ᚺ", "phonetic": "H",
                "meaning": "Disruption, natural forces, uncontrolled change",
                "reversed_meaning": "Cannot be reversed - transformative force",
                "element": "Water", "deity": "Hel"
            },
            {
                "name": "Nauthiz", "symbol": "ᚾ", "phonetic": "N",
                "meaning": "Need, necessity, endurance, constraint that teaches",
                "reversed_meaning": "Unnecessary suffering, poor planning",
                "element": "Fire", "deity": "Norns"
            },
            {
                "name": "Isa", "symbol": "ᛁ", "phonetic": "I",
                "meaning": "Ice, stillness, patience, things frozen in time",
                "reversed_meaning": "Cannot be reversed - represents stasis",
                "element": "Water", "deity": "Skadi"
            },
            {
                "name": "Jera", "symbol": "ᛃ", "phonetic": "J/Y",
                "meaning": "Harvest, cycles, reward for effort, good timing",
                "reversed_meaning": "Cannot be reversed - natural cycles",
                "element": "Earth", "deity": "Freyr"
            },
            {
                "name": "Eihwaz", "symbol": "ᛇ", "phonetic": "EI",
                "meaning": "Yew tree, death/rebirth, endurance, spiritual growth",
                "reversed_meaning": "Cannot be reversed - axis of worlds",
                "element": "Earth", "deity": "Odin"
            },
            {
                "name": "Perthro", "symbol": "ᛈ", "phonetic": "P",
                "meaning": "Mystery, chance, fate, hidden knowledge",
                "reversed_meaning": "Secrets revealed, poor luck",
                "element": "Water", "deity": "Norns"
            },
            {
                "name": "Algiz", "symbol": "ᛉ", "phonetic": "Z",
                "meaning": "Protection, higher self, spiritual connection",
                "reversed_meaning": "Vulnerability, disconnection from divine",
                "element": "Air", "deity": "Heimdall"
            },
            {
                "name": "Sowilo", "symbol": "ᛊ", "phonetic": "S",
                "meaning": "Sun, success, vitality, life force",
                "reversed_meaning": "Cannot be reversed - pure positive energy",
                "element": "Fire", "deity": "Baldr"
            },
            {
                "name": "Tiwaz", "symbol": "ᛏ", "phonetic": "T",
                "meaning": "Warrior, justice, honor, sacrifice for greater good",
                "reversed_meaning": "Injustice, dishonor, failed courage",
                "element": "Air", "deity": "Tyr"
            },
            {
                "name": "Berkano", "symbol": "ᛒ", "phonetic": "B",
                "meaning": "Birch tree, new beginnings, growth, fertility",
                "reversed_meaning": "Stagnation, lack of growth, family problems",
                "element": "Earth", "deity": "Frigg"
            },
            {
                "name": "Ehwaz", "symbol": "ᛖ", "phonetic": "E",
                "meaning": "Horse, partnership, trust, gradual progress",
                "reversed_meaning": "Mistrust, lack of progress, broken partnerships",
                "element": "Earth", "deity": "Freyr"
            },
            {
                "name": "Mannaz", "symbol": "ᛗ", "phonetic": "M",
                "meaning": "Humanity, social order, intelligence, cooperation",
                "reversed_meaning": "Selfishness, isolation, enemies",
                "element": "Air", "deity": "Odin"
            },
            {
                "name": "Laguz", "symbol": "ᛚ", "phonetic": "L",
                "meaning": "Water, intuition, flow, psychic abilities",
                "reversed_meaning": "Confusion, poor intuition, stagnant emotions",
                "element": "Water", "deity": "Njord"
            },
            {
                "name": "Ingwaz", "symbol": "ᛜ", "phonetic": "NG",
                "meaning": "Fertility, completion, inner growth, potential realized",
                "reversed_meaning": "Cannot be reversed - internal completion",
                "element": "Earth", "deity": "Ing"
            },
            {
                "name": "Dagaz", "symbol": "ᛞ", "phonetic": "D",
                "meaning": "Dawn, awakening, breakthrough, new day",
                "reversed_meaning": "Cannot be reversed - breakthrough energy",
                "element": "Fire", "deity": "Baldr"
            },
            {
                "name": "Othala", "symbol": "ᛟ", "phonetic": "O",
                "meaning": "Heritage, home, ancestral wisdom, true wealth",
                "reversed_meaning": "Prejudice, clinging to past, family disputes",
                "element": "Earth", "deity": "Odin"
            }
        ]

    def create_reading(self, spread_type: str = "single", **kwargs) -> RunicReading:
        """Create a runic reading with specified spread"""
        spreads = {
            "single": RuneSpread.single_rune(),
            "three_norns": RuneSpread.three_norns(),
            "five_cross": RuneSpread.five_cross(),
            "seven_chakras": RuneSpread.seven_chakras()
        }

        if spread_type not in spreads:
            spread_type = "single"

        spread_positions = spreads[spread_type]
        num_runes = len(spread_positions)

        # Select random runes
        selected_runes = random.sample(self.runes_data, num_runes)

        # Create RuneElement objects with random reversals
        rune_elements = []
        for rune_data in selected_runes:
            # Some runes cannot be reversed
            can_reverse = rune_data["reversed_meaning"] != f"Cannot be reversed - {rune_data['meaning'].split(',')[0].lower()}" and \
                         "Cannot be reversed" not in rune_data["reversed_meaning"]

            is_reversed = can_reverse and random.choice([True, False])

            rune_element = RuneElement(
                identifier=rune_data["name"],  # Use name as identifier
                name=rune_data["name"],
                symbol=rune_data["symbol"],
                description=rune_data["meaning"],  # Use meaning as description
                phonetic=rune_data["phonetic"],
                element=rune_data["element"],
                deity=rune_data["deity"],
                reversed_meaning=rune_data["reversed_meaning"],
                is_reversed=is_reversed
            )
            rune_elements.append(rune_element)

        return RunicReading(rune_elements, spread_type.title().replace('_', ' '), spread_positions)

    def get_all_elements(self) -> List[DivinationElement]:
        """Get all runes as divination elements"""
        elements = []
        for rune_data in self.runes_data:
            element = RuneElement(
                identifier=rune_data["name"],
                name=rune_data["name"],
                symbol=rune_data["symbol"],
                description=rune_data["meaning"],
                phonetic=rune_data["phonetic"],
                element=rune_data["element"],
                deity=rune_data["deity"],
                reversed_meaning=rune_data["reversed_meaning"]
            )
            elements.append(element)
        return elements

    def get_element_by_identifier(self, identifier: str) -> Optional[DivinationElement]:
        """Get a specific rune by its identifier (name)"""
        for rune_data in self.runes_data:
            if rune_data["name"].lower() == identifier.lower():
                return RuneElement(
                    identifier=rune_data["name"],
                    name=rune_data["name"],
                    symbol=rune_data["symbol"],
                    description=rune_data["meaning"],
                    phonetic=rune_data["phonetic"],
                    element=rune_data["element"],
                    deity=rune_data["deity"],
                    reversed_meaning=rune_data["reversed_meaning"]
                )
        return None

    def get_element_by_name(self, name: str) -> Optional[DivinationElement]:
        """Get a specific rune by name (alias for get_element_by_identifier)"""
        return self.get_element_by_identifier(name)

    def get_system_name(self) -> str:
        """Get the display name of this divination system"""
        return "Elder Futhark Runes"

    def get_system_description(self) -> str:
        """Get a description of this divination system"""
        return ("The Elder Futhark is the oldest form of runic alphabets, used by Germanic tribes "
                "between the 2nd and 8th centuries CE. These 24 sacred symbols carry deep spiritual "
                "significance and were believed to possess magical properties, serving as keys to "
                "divine wisdom and Norse mythology.")


# Convenience functions for creating runic readings
def cast_single_rune() -> RunicReading:
    """Cast a single rune for guidance"""
    system = RunicSystem()
    return system.create_reading("single")


def cast_three_norns() -> RunicReading:
    """Cast the Three Norns spread (Past, Present, Future)"""
    system = RunicSystem()
    return system.create_reading("three_norns")


def cast_five_cross() -> RunicReading:
    """Cast the Five Rune Cross spread"""
    system = RunicSystem()
    return system.create_reading("five_cross")


def cast_seven_chakras() -> RunicReading:
    """Cast the Seven Chakras spread"""
    system = RunicSystem()
    return system.create_reading("seven_chakras")
