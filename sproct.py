import re
import argparse
from collections import namedtuple, defaultdict

_word_regex = re.compile(r'\w+')
_word_punct_regex = re.compile(r'\w+|[^\w\s]+')

_Line = namedtuple('Line', ['character', 'text_lines'])

class Line(_Line):
    @property
    def words(self):
        raw = ' '.join(self.text_lines)
        words = _word_regex.findall(raw)
        return [w.lower() for w in words]

    @property
    def text(self):
        return '\n'.join(self.text_lines)

class LineBuilder(object):
    def __init__(self, character, text_lines=None):
        self.character = character
        self.text_lines = text_lines if text_lines is not None else []

    def append(self, text_line):
        self.text_lines.append(text_line)

    def complete(self):
        return Line(str(self.character),
                    tuple(str(l) for l in self.text_lines))

class Play(object):
    def __init__(self, lines):
        self.lines = lines
        self.characters = set(l.character for l in lines)

        character_index = defaultdict(list)
        for l in lines:
            character_index[l.character].append(l)
        self.character_index = character_index

    def character_line_count(self, character):
        return len(self.character_index.get(character, []))

    def character_word_count(self, character):
        character_lines = self.character_index.get(character, [])
        return sum(1 for l in character_lines for w in l.words)

    def reconstitute(self):
        fulltext = []
        for line in self.lines:
            fulltext.append(line.character)
            fulltext.append(line.text)
        return '\n'.join(fulltext)

def segment(text_lines, character_split):
    lines = []
    partial_line = LineBuilder('PREFACE_TEXT')
    for text_line in text_lines:
        character, line = character_split(text_line)
        if character:
            lines.append(partial_line.complete())
            partial_line = LineBuilder(character)
        if line:
            partial_line.append(line)
    if partial_line.complete() != lines[-1]:
        lines.append(partial_line.complete())
    return lines

def loadlines(path, character_split):
    with open(path) as f:
        raw_lines = f.readlines()
    return segment(raw_lines, character_split)

def character_allcaps_split(text_line):
    if text_line.strip().isupper():
        return (text_line.strip(), '')
    else:
        return ('', text_line.strip())

def get_args():
    parser = argparse.ArgumentParser(
        description='Count words in a play.'
    )

    sub = parser.add_subparsers()
    cwords = sub.add_parser(
        'character_word_count',
        help='Count the number of words a character has in the given play.'
    )
    cwords.add_argument('text', type=str, help='The play text file.')
    cwords.add_argument(
        'character_name', type=str, help="The character's name."
    )
    return parser.parse_args()

if __name__ == '__main__':
    args = get_args()
    lines = loadlines(args.text, character_allcaps_split)
    play = Play(lines)
    print(play.character_word_count(args.character_name))
