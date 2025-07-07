"""
Trigram utility functions for The Oracle application.
"""


def get_trigram_info():
    """Get information about the 8 trigrams"""
    trigrams = [
        {
            'id': 'heaven',
            'name': 'Heaven',
            'chinese': '干 | qián',
            'symbol': '☰',
            'lines': '≡',
            'attributes': ['Creative', 'Strong', 'Active', 'Light-giving', 'Warming', 'Summer'],
            'description': 'The Creative principle, representing pure yang energy, strength, and the power of heaven. '
                + 'It embodies the primal creative force of the universe, the father archetype, and divine '
                + 'inspiration. One of the three powers of Taoist cosmology. Associated with leadership, '
                + 'authority, and the drive to achieve. In the body, it governs the head and lungs. Its season '
                + 'is late autumn/early winter, direction is northwest, and it represents the time from 9-11 PM. '
                + 'This trigram speaks of perseverance, determination, and the courage to initiate new ventures. '
                + 'When prominent in a reading, it suggests taking charge, being proactive, and trusting in '
                + 'your natural leadership abilities.'
        },
        {
            'id': 'earth',
            'name': 'Earth',
            'chinese': '坤 | kūn',
            'symbol': '☷',
            'lines': '☷',
            'attributes': ['Receptive', 'Yielding', 'Nurturing', 'Devoted', 'Resting', 'Winter'],
            'description': 'The Receptive principle, representing pure yin energy, yielding strength, and the '
               + 'power of earth. It embodies the nurturing mother archetype, unconditional support, and the '
               + 'fertile ground from which all life springs. One of the three powers of Taoist cosmology. '
               + 'Associated with patience, devotion, and the wisdom of knowing when to yield. In the body, '
               + 'it governs the belly and reproductive organs. Its season is late summer, direction is '
               + 'southwest, and it represents the time from 1-3 PM. This trigram teaches the power of '
               + 'receptivity, the strength found in gentleness, and the importance of providing stable '
               + 'foundations. When prominent in a reading, it suggests embracing supportive roles, '
               + 'practicing patience, and trusting in the natural flow of events.'
        },
        {
            'id': 'thunder',
            'name': 'Thunder',
            'chinese': '震 | zhèn',
            'symbol': '☳',
            'lines': '☳',
            'attributes': ['Arousing', 'Movement', 'Initiative', 'Eldest Son', 'Storming', 'Winter'],
            'description': 'The Arousing, representing movement, initiative, and the power of thunder and '
                + 'lightning. It embodies sudden awakening, decisive action, and the explosive energy that '
                + 'breaks through stagnation. As the eldest son, it carries the pioneering spirit and the '
                + 'courage to forge new paths. In the body, it governs the feet and liver. Its season is '
                + 'spring, direction is east, and it represents the time from 5-7 AM. This trigram speaks '
                + 'of breakthrough moments, the power of righteous action, and the energy needed to '
                + 'overcome obstacles. When prominent in a reading, it suggests bold moves, embracing '
                + 'change, and acting on sudden inspirations with confidence.'
        },
        {
            'id': 'water',
            'name': 'Water',
            'chinese': '坎 | kǎn',
            'symbol': '☵',
            'lines': '☵',
            'attributes': ['Abysmal', 'Dangerous', 'Flowing', 'Middle Son', 'Pooling', 'Autumn'],
            'description': 'The Abysmal, representing danger, flowing water, and the power of the deep. '
                + 'It embodies the middle son\'s role as mediator, the wisdom gained through hardship, and '
                + 'the persistence of water that eventually wears down stone. One of the three powers of '
                + 'Taoist cosmology. Associated with intuition, adaptability, and the courage to navigate '
                + 'difficult situations. In the body, it governs the kidneys and ears. Its season is winter, '
                + 'direction is north, and it represents the time from 11 PM-1 AM. This trigram teaches '
                + 'about resilience in adversity, the power of consistency, and finding opportunity within '
                + 'challenge. When prominent in a reading, it suggests careful navigation of difficulties, '
                + 'trusting your intuition, and maintaining steady progress despite obstacles.'
        },
        {
            'id': 'mountain',
            'name': 'Mountain',
            'chinese': '艮 | gèn',
            'symbol': '☶',
            'lines': '☶',
            'attributes': ['Keeping Still', 'Meditation', 'Youngest Son', 'Stillness', 'Jutting', 'Autumn'],
            'description': 'Keeping Still, representing meditation, stillness, and the immovable power of '
                + 'mountains. It embodies the youngest son\'s wisdom of knowing when to stop, the power of '
                + 'contemplation, and the strength found in inner peace. Associated with boundaries, '
                + 'self-reflection, and the ability to remain centered amidst chaos. In the body, it governs '
                + 'the hands and stomach. Its season is late winter/early spring, direction is northeast, '
                + 'and it represents the time from 3-5 AM. This trigram teaches the value of restraint, '
                + 'the importance of timing, and the profound wisdom that comes from stillness. When '
                + 'prominent in a reading, it suggests taking time for reflection, establishing healthy '
                + 'boundaries, and finding strength through inner stability.'
        },
        {
            'id': 'wind',
            'name': 'Wind',
            'chinese': '巽 | xùn',
            'symbol': '☴',
            'lines': '☴',
            'attributes': ['Gentle', 'Penetrating', 'Eldest Daughter', 'Wood', 'Dispersing', 'Summer'],
            'description': 'The Gentle, representing penetration, flexibility, and the power of wind and wood. '
                + 'It embodies the eldest daughter\'s role as gentle leader, the persistence that eventually '
                + 'penetrates all obstacles, and the wisdom of adapting to circumstances. Associated with '
                + 'influence, communication, and the ability to work with others harmoniously. In the body, '
                + 'it governs the thighs and gallbladder. Its season is late spring/early summer, direction '
                + 'is southeast, and it represents the time from 7-9 AM. This trigram teaches about subtle '
                + 'influence, the power of consistency, and achieving goals through gentle persistence rather '
                + 'than force. When prominent in a reading, it suggests working with others, using gentle '
                + 'persuasion, and allowing your influence to grow naturally over time.'
        },
        {
            'id': 'fire',
            'name': 'Fire',
            'chinese': '离 | lí',
            'symbol': '☲',
            'lines': '☲',
            'attributes': ['Clinging', 'Light', 'Middle Daughter', 'Brightness', 'Dancing', 'Spring'],
            'description': 'The Clinging, representing light, beauty, and the illuminating power of fire. '
                + 'It embodies the middle daughter\'s role as illuminator, the power of clarity and insight, '
                + 'and the warm energy that brings people together. Associated with intelligence, creativity, '
                + 'and the ability to see truth clearly. In the body, it governs the eyes and heart. Its '
                + 'season is summer, direction is south, and it represents the time from 11 AM-1 PM. This '
                + 'trigram teaches about clarity of vision, the importance of maintaining inner light, and '
                + 'the power of truth to transform situations. When prominent in a reading, it suggests '
                + 'seeking clarity, embracing your creative gifts, and allowing your inner light to guide '
                + 'both yourself and others.'
        },
        {
            'id': 'lake',
            'name': 'Lake',
            'chinese': '兑 | duì',
            'symbol': '☱',
            'lines': '☱',
            'attributes': ['Joyous', 'Youngest Daughter', 'Pleasure', 'Marsh', 'Engulfing', 'Spring'],
            'description': 'The Joyous, representing joy, pleasure, and the reflective power of lakes and '
                + 'marshes. It embodies the youngest daughter\'s gift of bringing happiness, the power of '
                + 'authentic expression, and the wisdom found in celebration. Associated with communication, '
                + 'social harmony, and the ability to find joy even in simple moments. In the body, it '
                + 'governs the mouth and lungs. Its season is autumn, direction is west, and it represents '
                + 'the time from 5-7 PM. This trigram teaches about the importance of joy, the power of '
                + 'words to heal or harm, and the value of maintaining an open, receptive heart. When '
                + 'prominent in a reading, it suggests embracing joy, expressing yourself authentically, '
                + 'and creating harmony through positive communication.'
        }
    ]
    return trigrams
