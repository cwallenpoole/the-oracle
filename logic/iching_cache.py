"""
I Ching data caching module for improved performance.

This module pre-loads and caches all hexagram data to avoid repeated file I/O
and parsing operations. It provides a significant performance improvement over
the original implementation.
"""

import os
import re
import time
from typing import Dict, Optional
from logic.iching import IChingHexagram, IChingAbout, IChingLine
from docarray import DocList


class IChingCache:
    """Cache for I Ching hexagram data with lazy loading and refresh capabilities"""

    def __init__(self):
        self._cache: Dict[int, IChingHexagram] = {}
        self._file_path = os.path.join(os.path.dirname(__file__), 'I-Ching-texts.md')
        self._last_loaded = 0
        self._file_mtime = 0

    def _should_refresh(self) -> bool:
        """Check if cache should be refreshed based on file modification time"""
        try:
            current_mtime = os.path.getmtime(self._file_path)
            return current_mtime != self._file_mtime
        except OSError:
            return True

    def _load_all_hexagrams(self) -> None:
        """Load and parse all hexagrams from the file at once"""
        try:
            with open(self._file_path, 'r', encoding='utf-8') as file:
                text = file.read()

            # Update file modification time
            self._file_mtime = os.path.getmtime(self._file_path)

            # Parse all hexagrams at once
            self._cache = self._parse_all_hexagrams(text)
            self._last_loaded = time.time()

        except Exception as e:
            print(f"Error loading I Ching data: {e}")
            # Keep existing cache if available
            if not self._cache:
                self._cache = {}

    def _parse_all_hexagrams(self, text: str) -> Dict[int, IChingHexagram]:
        """Parse all hexagrams from the text efficiently"""
        hexagrams = {}

        # Find all hexagram sections at once
        hexagram_pattern = re.compile(
            r"^##\s+(\d+)\.\s+(.+?)\s+(䷀|䷁|䷂|䷃|䷄|䷅|䷆|䷇|䷈|䷉|䷊|䷋|䷌|䷍|䷎|䷏|䷐|䷑|䷒|䷓|䷔|䷕|䷖|䷗|䷘|䷙|䷚|䷛|䷜|䷝|䷞|䷟|䷠|䷡|䷢|䷣|䷤|䷥|䷦|䷧|䷨|䷩|䷪|䷫|䷬|䷭|䷮|䷯|䷰|䷱|䷲|䷳|䷴|䷵|䷶|䷷|䷸|䷹|䷺|䷻|䷼|䷽|䷾|䷿)$",
            re.MULTILINE
        )

        matches = list(hexagram_pattern.finditer(text))

        for i, match in enumerate(matches):
            number = int(match.group(1))
            title = match.group(2).strip()
            symbol = match.group(3).strip()

            # Get the content from this match to the next (or end of file)
            start = match.start()
            if i + 1 < len(matches):
                end = matches[i + 1].start()
            else:
                end = len(text)

            section = text[start:end].strip()

            try:
                hexagram = self._parse_hexagram_section(section, number, title, symbol)
                if hexagram:
                    hexagrams[number] = hexagram
            except Exception as e:
                print(f"Error parsing hexagram {number}: {e}")
                continue

        return hexagrams

    def _parse_hexagram_section(self, section: str, number: int, title: str, symbol: str) -> Optional[IChingHexagram]:
        """Parse a single hexagram section"""
        try:
            # Split by major sections
            parts = section.split('### THE JUDGMENT')
            if len(parts) != 2:
                return None

            [pre_judge, post_judge] = parts

            # Extract above/below and description
            above_match = re.search(r"> above\s+(.+)", pre_judge)
            below_match = re.search(r"> below\s+(.+)", pre_judge)
            description_match = re.search(r"> below.+\n\n(.+?)(?=\n### THE JUDGMENT)", pre_judge, re.DOTALL)

            above = above_match.group(1).strip() if above_match else ""
            below = below_match.group(1).strip() if below_match else ""
            description = description_match.group(1).strip() if description_match else ""

            # Split judgment and image sections
            image_split = post_judge.split('### THE IMAGE')
            if len(image_split) != 2:
                return None

            [judge_section, post_image] = image_split

            # Parse judgment
            judge_quote, judge_text = self._parse_section_content(judge_section)

            # Parse image
            lines_split = post_image.split('#### THE LINES')
            if len(lines_split) != 2:
                return None

            [image_section, lines_section] = lines_split
            image_quote, image_text = self._parse_section_content(image_section)

            # Parse lines
            lines = self._parse_lines(lines_section)

            return IChingHexagram(
                Symbol=symbol,
                Number=number,
                Title=title,
                About=IChingAbout(
                    Above=above,
                    Below=below,
                    Description=description
                ),
                Judgement=IChingLine(
                    Quote="\n".join(judge_quote),
                    Text="\n".join(judge_text)
                ),
                Image=IChingLine(
                    Quote="\n".join(image_quote),
                    Text="\n".join(image_text)
                ),
                Lines=lines,
                Content=section,
            )

        except Exception as e:
            print(f"Error parsing hexagram {number} section: {e}")
            return None

    def _parse_section_content(self, section: str) -> tuple[list, list]:
        """Parse quote and text content from a section"""
        quotes = []
        texts = []

        for line in section.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith('>'):
                quotes.append(line.strip('> #').strip())
            else:
                texts.append(line)

        return quotes, texts

    def _parse_lines(self, lines_section: str) -> list:
        """Parse the lines section into individual line objects"""
        lines = []

        if not lines_section:
            return lines

        # Find all line patterns
        line_pattern = re.compile(r"(?P<ln>(^>[^\n]+\n)+)(?P<txt>[^>]+)", re.DOTALL | re.MULTILINE)

        for match in line_pattern.finditer(lines_section):
            quote_lines = match.group('ln').strip().split('\n')
            # Remove the '>' and clean up each line, skip the first line (which is usually just '>')
            cleaned_quotes = []
            for line in quote_lines[1:]:  # Skip first line
                cleaned_line = line.strip().lstrip('> ').strip()
                if cleaned_line:
                    cleaned_quotes.append(cleaned_line)

            quote = "\n".join(cleaned_quotes)
            text = match.group('txt').strip()

            lines.append(IChingLine(Quote=quote, Text=text))

        return lines

    def get_hexagram(self, number: int) -> Optional[IChingHexagram]:
        """Get a hexagram by number, loading cache if needed"""
        if not isinstance(number, int) or number < 1 or number > 64:
            return None

        # Check if we need to load or refresh cache
        if not self._cache or self._should_refresh():
            self._load_all_hexagrams()

        return self._cache.get(number)

    def get_all_hexagrams(self) -> Dict[int, IChingHexagram]:
        """Get all hexagrams, loading cache if needed"""
        if not self._cache or self._should_refresh():
            self._load_all_hexagrams()

        return self._cache.copy()

    def get_hexagram_symbols(self) -> Dict[int, str]:
        """Get mapping of hexagram numbers to symbols"""
        if not self._cache or self._should_refresh():
            self._load_all_hexagrams()

        return {num: hex_obj.Symbol for num, hex_obj in self._cache.items()}

    def clear_cache(self) -> None:
        """Clear the cache to force reload"""
        self._cache.clear()
        self._last_loaded = 0
        self._file_mtime = 0

    def get_cache_stats(self) -> dict:
        """Get cache statistics for debugging"""
        return {
            'hexagrams_loaded': len(self._cache),
            'last_loaded': self._last_loaded,
            'file_mtime': self._file_mtime,
            'cache_age_seconds': time.time() - self._last_loaded if self._last_loaded else 0
        }


# Global cache instance
_cache_instance = None


def get_cache() -> IChingCache:
    """Get the global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = IChingCache()
    return _cache_instance


def get_hexagram_section_cached(number: int) -> Optional[IChingHexagram]:
    """Get a hexagram section using the cache - drop-in replacement for iching.get_hexagram_section"""
    return get_cache().get_hexagram(number)


def get_all_hexagrams_cached() -> Dict[int, IChingHexagram]:
    """Get all hexagrams using the cache"""
    return get_cache().get_all_hexagrams()


def get_hexagram_symbols_cached() -> Dict[int, str]:
    """Get hexagram symbols using the cache"""
    return get_cache().get_hexagram_symbols()


def clear_cache() -> None:
    """Clear the cache (useful for testing or if file is updated)"""
    get_cache().clear_cache()


def get_cache_stats() -> dict:
    """Get cache statistics"""
    return get_cache().get_cache_stats()
