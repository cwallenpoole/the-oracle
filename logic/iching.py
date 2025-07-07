from docarray import BaseDoc, DocList

import os
import random
import re
import pdb

class IChingLine(BaseDoc):
    Quote: str
    Text: str

    def __str__(self):
        return f'>> {self.Quote}\n{self.Text}'

class IChingAbout(BaseDoc):
    Above: str
    Below: str
    Description: str

class IChingHexagram(BaseDoc):
    Symbol: str
    Number: int
    Title: str
    About: IChingAbout
    Judgement: IChingLine
    Image: IChingLine
    Lines: DocList
    Content: str

    def __str__(self):
        base = f'{self.Number} {self.Title}\n{self.About.Above}\n{self.About.Below}\n{self.About.Description}'
        return base

class Reading:
    Current: IChingHexagram
    Future: IChingHexagram

    def __init__(self):
        self.Current = None
        self.Future = None

    def has_transition(self):
        return self.Future is not None

    def __str__(self):
        base = f'*{self.Current.Number} {self.Current.Title}*\n{self.Current.About.Above}\n{self.Current.About.Below}\n{self.Current.About.Description}'
        if self.has_transition():
            return f'{base}\ntransitioning to\n*{self.Future.Number} {self.Future.Title}*\n{self.Future.About.Above}\n{self.Future.About.Below}\n{self.Future.About.Description}'
        return base

def cast_hexagrams() -> Reading:
    current = []
    secondary = []
    for i in range(0, 6):
        s = random.choices((0, 1), k = 3)
        s.sort()
        to_append = 'G'
        if s == [1, 1, 1]:
            current.append('G')
            secondary.append('L')
        elif s == [0, 0, 0]:
            current.append('L')
            secondary.append('G')
        else:
            if s == [0, 1, 1]:
                to_append = 'L'
            current.append(to_append)
            secondary.append(to_append)

    reading = Reading()
    reading.Current = get_hexagram_section_from_hexagram(current)
    if current != secondary:
        reading.Future = get_hexagram_section_from_hexagram(secondary)
    return reading

def get_text_from_hexagram(hexagram):
    return hexagram.split(' ')[1]

def get_num_from_hexagram(hexagram):
    return int(hexagram.split(' ')[0])

def get_hexagram(key):
    vals = {
        'LLLLLL': '1 Creative', 'GGGGGG': '2 Receptive', 'GLGGGL': '3 Difficulty', 'LGGGLG': '4 Folly',
        'GLGLLL': '5 Waiting', 'LLLGLG': '6 Conflict', 'GGGGLG': '7 Army', 'GLGGGG': '8 Union',
        'LGLLLL': '14 Possession', 'LLLGLL': '10 Treading', 'GGGLLL': '11 Peace', 'LLLGGG': '12 Standstill',
        'LLLLGL': '13 Fellowship', 'GGGLGG': '15 Modesty', 'GGLGGG': '16 Enthusiasm', 'GLLGGL': '17 Following',
        'LGGLLG': '18 Decay', 'GGGGLL': '19 Approach', 'LLGGGG': '20 View', 'LGLGGL': '21 Biting',
        'LGGLGL': '22 Grace', 'LGGGGG': '23 Splitting', 'GGGGGL': '24 Return', 'LLLGGL': '25 Innocence',
        'LGGLLL': '26 Taming', 'LGGGGL': '27 Mouth', 'GLLLLG': '28 Preponderance', 'GLGGLG': '29 Abysmal',
        'LGLLGL': '30 Clinging', 'GLLLGG': '31 Influence', 'GGLLLG': '32 Duration', 'LLLLGG': '33 Retreat',
        'GGLLLL': '34 Power', 'LGLGGG': '35 Progress', 'GGGLGL': '36 Darkening', 'LLGLGL': '37 Family',
        'LGLGLL': '38 Opposition', 'GLGLGG': '39 Obstruction', 'GGLGLG': '40 Deliverance',
        'LGGGLL': '41 Decrease', 'LLGGGL': '42 Increase', 'GLLLLL': '43 Resoluteness', 'LLLLLG': '44 Coming',
        'GLLGGG': '45 Gathering', 'GGGLLG': '46 Pushing', 'GLLGLG': '47 Oppression', 'GLGLLG': '48 Well',
        'GLLLGL': '49 Revolution', 'LGLLLG': '50 Caldron', 'GGLGGL': '51 Arousing', 'LGGLGG': '52 Still',
        'LLGLGG': '53 Development', 'GGLGLL': '54 Marrying', 'GGLLGL': '55 Abundance', 'LGLLGG': '56 Wanderer',
        'LLGLLG': '57 Gentle', 'GLLGLL': '58 Joyous', 'LLGGLG': '59 Dispersion', 'GLGGLL': '60 Limitation',
        'LLGGLL': '61 Truth', 'GGLLGG': '62 Small', 'GLGLGL': '63 After', 'LGLGLG': '64 Before'
    }
    return vals.get(key, None)

def get_hexagram_section_from_hexagram(current):
    return get_hexagram_section(get_num_from_hexagram(get_hexagram(''.join(current))))

def get_text():
    with open(os.path.join(os.path.dirname(__file__), 'I-Ching-texts.md'), 'r') as file:
        text = file.read()
    return text

def get_hgram_text(hgram: IChingHexagram):
    return hgram.Content

def get_hexagram_section(number):
    text = get_text()
    # Find the section for the given number
    pattern = re.compile(rf"^##\s+{number}\.\s+(?P<title>.+?)\s+(?P<symbol>䷀|䷁|䷂|䷃|䷄|䷅|䷆|䷇|䷈|䷉|䷊|䷋|䷌|䷍|䷎|䷏|䷐|䷑|䷒|䷓|䷔|䷕|䷖|䷗|䷘|䷙|䷚|䷛|䷜|䷝|䷞|䷟|䷠|䷡|䷢|䷣|䷤|䷥|䷦|䷧|䷨|䷩|䷪|䷫|䷬|䷭|䷮|䷯|䷰|䷱|䷲|䷳|䷴|䷵|䷶|䷷|䷸|䷹|䷺|䷻|䷼|䷽|䷾|䷿)$", re.MULTILINE)
    match = pattern.search(text)

    if not match:
        return None
    start = match.start()
    # Find the start of the next section or end of file
    next_section = re.search(r"^##\s+\d+\.", text[start+1:], re.MULTILINE)
    end = start + next_section.start() if next_section else len(text)
    section = text[start:end]

    # Title
    title = match.group('title').strip()
    symbol = match.group('symbol').strip()

    parts = section.split('### THE JUDGMENT')
    if len(parts) != 2:
        import pdb; pdb.set_trace()
    [pre_judge, post_judge] = parts
    # About
    above = re.search(r"> above\s+(.+)", pre_judge)
    below = re.search(r"> below\s+(.+)", pre_judge)
    description_match = re.search(r"> below.+\n\n(.+?)(?=\n### THE JUDGMENT)", pre_judge, re.DOTALL)
    description = description_match.group(1).strip() if description_match else ""


    [judge_section, post_image] = post_judge.split('### THE IMAGE')

    judge_quote = []
    judge_text = []
    for line in judge_section.splitlines():
        if not line:
            continue
        if line.startswith('>'):
            judge_quote.append(line.strip('> #'))
        else:
            judge_text.append(line)

    image_quote = []
    image_text = []
    [image_section, lines_section] = post_image.split('#### THE LINES')
    for line in image_section.splitlines():
        if not line:
            continue
        if line.startswith('>'):
            image_quote.append(line.strip('> #'))
        else:
            image_text.append(line)

    # Lines
    lines = []
    if lines_section:
        for m in re.finditer(r"(?P<ln>(^>[^\n]+\n)+)(?P<txt>[^>]+)", lines_section, re.DOTALL | re.MULTILINE):
            quote = "\n".join([l.strip() for l in m.group('ln').splitlines()[1:]])
            text = m.group('txt').strip()
            lines.append(IChingLine(Quote=quote, Text=text))

    docLines = DocList[IChingLine](lines)
    return IChingHexagram(
        Symbol = symbol,
        Number = int(number),
        Title = title,
        About = IChingAbout(
            Above = above.group(1).strip() if above else "",
            Below = below.group(1).strip() if below else "",
            Description =  description
        ),
        Judgement = IChingLine(
            Quote = "\n".join(judge_quote),
            Text = "\n".join(judge_text)
        ),
        Image = IChingLine(
            Quote = "\n".join(image_quote),
            Text = "\n".join(image_text)
        ),
        Lines=lines,
        Content = section,
    )

if __name__ == '__main__':
    print(repr(cast_hexagrams()))
