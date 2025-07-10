# Wiki Synonyms System

The Oracle wiki supports synonyms - alternative names that redirect to canonical entries. This allows multiple names to point to the same wiki entry.

## How It Works

When a user accesses a wiki entry that is defined as a synonym, they are automatically redirected to the canonical entry. For example:

- `/wiki/ragnarok` → redirects to `/wiki/battle_of_ragnarok`
- `/wiki/ragnarök` → redirects to `/wiki/battle_of_ragnarok`
- `/wiki/all-father` → redirects to `/wiki/odin`

## Configuration

Synonyms are defined in `wiki/synonyms.json`. The format is:

```json
{
    "synonym_filename": {
        "canonical": "canonical_filename",
        "category": "category_name"
    }
}
```

### Example:
```json
{
    "ragnarok": {
        "canonical": "battle_of_ragnarok",
        "category": "events"
    },
    "all_father": {
        "canonical": "odin",
        "category": "characters"
    }
}
```

## Managing Synonyms

### Command Line Tool

Use `scripts/manage_synonyms.py` to manage synonyms:

```bash
# List all synonyms
python scripts/manage_synonyms.py list

# Add a new synonym
python scripts/manage_synonyms.py add "Ragnarök" "Battle of Ragnarök" "events"

# Remove a synonym
python scripts/manage_synonyms.py remove "Ragnarök"
```

### Programmatic API

```python
from utils.wiki_utils import add_synonym, remove_synonym, list_synonyms

# Add a synonym
add_synonym("World Tree", "Yggdrasil", "places")

# Remove a synonym
remove_synonym("World Tree")

# List all synonyms
synonyms = list_synonyms()
```

## Categories

Valid categories for synonyms:
- `characters` - Mythological figures, deities, heroes
- `events` - Historical or mythological events
- `places` - Locations, realms, geographical features
- `concepts` - Abstract ideas, philosophies, practices
- `divination_types` - Types of divination systems

## Link Processing

When wiki links are created from bracketed text like `[Ragnarök]`, the system:

1. Checks if the term is a synonym
2. If it is, creates a placeholder for the canonical entry (if needed)
3. Links to the canonical entry using the original text as the link text

This means `[Ragnarök]` becomes `<a href="/wiki/battle_of_ragnarok">Ragnarök</a>`.

## Best Practices

1. **Use descriptive canonical names**: Prefer "Battle of Ragnarök" over just "Ragnarök"
2. **Include common variations**: Add synonyms for different spellings, translations, and common names
3. **Maintain consistency**: Use the same canonical entry for related synonyms
4. **Document relationships**: Consider noting synonyms in the canonical entry's content

## Example Synonyms

Current synonyms in the system:

- **Ragnarök**: `ragnarok`, `ragnarök`, `twilight_of_the_gods` → `battle_of_ragnarok`
- **Odin**: `all_father`, `allfather`, `all-father` → `odin`
- **Yggdrasil**: `world_tree` → `yggdrasil`

## Technical Implementation

The synonym system:

1. **Load time**: Synonyms are loaded from JSON on each request
2. **Resolution**: Names are resolved to canonical forms during link creation
3. **Redirects**: Direct URL access to synonyms triggers HTTP redirects
4. **Fallback**: If canonical entry doesn't exist, normal wiki creation process applies

This ensures that all references to the same concept, regardless of the name used, point to a single authoritative wiki entry.
