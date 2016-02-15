import re
import argparse
from functools import wraps
from collections import namedtuple, defaultdict, Hashable

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
                    tuple(str(l) for l in self.text_lines)
                    )

class Play(object):
    def __init__(self, lines):
        self.lines = lines

    @property
    def lines(self):
        return self._lines

    @lines.setter
    def lines(self, lines):
        self._lines = lines
        self._cache = {}

        character_index = defaultdict(list)
        for l in lines:
            character_index[l.character].append(l)
        self.character_index = character_index

    def _cached(func):
        fname = func.__name__

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            allargs = [fname]
            allargs.extend(args)
            allargs.extend(kwargs.items())
            if isinstance(allargs, Hashable):
                if allargs not in self._cache:
                    self._cache[allargs] = func(self, *args, **kwargs)
                return self._cache[allargs]
            return func(self, *args, **kwargs)
        return wrapper

    @_cached
    def character_line_count(self, character):
        return len(self.character_index.get(character, []))

    @_cached
    def character_word_count(self, character):
        character_lines = self.character_index.get(character, [])
        return sum(1 for l in character_lines for w in l.words)

    def character_average_words(self, character):
        return (self.character_word_count(character) *
                1.0 / self.character_line_count(character)
                )

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

class CharacterWordCount(object):
    def __init__(self, play):
        self.play = play

    def __call__(self, character=None):
        out = self.table if character is None else self.single
        return out(character)

    def wc_tuple(self, character):
        word = self.play.character_word_count(character)
        avg = self.play.character_average_words(character)
        lines = self.play.character_line_count(character)
        return word, avg, lines

    def single(self, character):
        out = 'Word counts for {}:\n  Total: {}  Average: {}  Lines: {}'
        word, avg, lines = self.wc_tuple(character)
        print out.format(character, word, avg, lines)

    def table(self, character=None):
        rows = [('Character', 'Words', 'Average', 'Lines')]
        names = sorted(self.play.character_index)
        rows.extend((n,) + self.wc_tuple(n) for n in names)

        rowtemplate = '  {row[0]: <{maxlen}}{row[1]: <{maxlen}}' \
                      '{row[2]: <{maxlen}}{row[3]: <{maxlen}}'

        maxlen = max(len(str(d)) for row in rows for d in row) + 2
        print 'Word counts for all characters.'
        print
        print rowtemplate.format(row=rows[0], maxlen=maxlen)
        print
        for row in rows[1:]:
            print rowtemplate.format(row=row, maxlen=maxlen)

def get_args():
    parser = argparse.ArgumentParser(description='Count words in a play.')

    sub = parser.add_subparsers()
    cwords = sub.add_parser(
        'character_word_count',
        help='Count the number of words a character speaks in the given play.'
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
    wc = CharacterWordCount(play)
    char = args.character_name
    wc(None if char == 'all' else char)
