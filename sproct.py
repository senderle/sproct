import re
import argparse
from functools import wraps
from collections import namedtuple, defaultdict, Hashable, Counter
from difflib import SequenceMatcher, Differ

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

    def get_lines(self, character=None):
        if character is None:
            return self.lines
        else:
            return self.character_index.get(character, [])

    def words(self, character=None):
        return ' '.join(' '.join(ln.words) for ln in self.get_lines(character))

    def regular_text(self, character=None):
        return self._reconstitute(character, line_attr='words', join=' '.join)

    def text(self, character=None):
        return self._reconstitute(character)

    def _reconstitute(self, character=None, line_attr='text', join='\n'.join):
        lines = self.get_lines(character)
        fulltext = []
        for line in lines:
            fulltext.append(line.character)
            fulltext.append(join(getattr(line, line_attr)))
        return join(fulltext)

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

        rowtemplate = '\t{row[0]: <{maxlen}}\t{row[1]: <{maxlen}}' \
                      '\t{row[2]: <{maxlen}}\t{row[3]: <{maxlen}}'

        maxlen = max(len(str(d)) for row in rows for d in row) + 2
        print 'Word counts for all characters.'
        print
        print rowtemplate.format(row=rows[0], maxlen=maxlen)
        print
        for row in rows[1:]:
            print rowtemplate.format(row=row, maxlen=maxlen)

def bag_of_ngrams(words, n=2):
    iters = [iter(words) for _ in range(n)]
    for n, it in enumerate(iters):
        for _ in range(n):
            next(it, None)
    return Counter(zip(*iters))

def norm(A, B=None):
    if B is None:
        B = [0 for _ in A]
    diff = [a - b for a, b in zip(A, B)]
    return dot(diff, diff) ** 0.5

def dot(A, B):
    return sum(a * b for a, b in zip(A, B))

def cosine_sim(A, B):
    n = norm(A) * norm(B)
    return norm if norm == 0 else dot(A, B) * 1.0 / n

class Commands(object):
    def __init__(self):
        parser = argparse.ArgumentParser(description='Count words in a play.')

        sub = parser.add_subparsers()
        cwords = sub.add_parser(
            'count', help='Count the number of words a character speaks in '
            'the given play.'
        )
        cwords.add_argument(
            'texts', nargs='+', type=str, help='The play text file or files.'
        )
        cwords.add_argument(
            '--character', '-c', type=str, help='The name of the character.',
            default=None
        )
        cwords.set_defaults(command=self.cwords)

        diff = sub.add_parser(
            'diff', help='Return the approximate degree of difference between '
            'two plays, at the character level, as a decimal fraction between '
            '0.0 and 1.0.'
        )
        diff.add_argument(
            'text_one', type=str, help='The first play text file.'
        )
        diff.add_argument(
            'text_two', type=str, help='The second play text file.'
        )
        diff.add_argument(
            '--character', '-c', type=str, help='The name of the character.',
            default=None
        )

        diff.set_defaults(command=self.diff)

        bobsim = sub.add_parser(
            'bobsim', help='Compare two plays, and identify lines longer '
            'than 74 words that have substantial similarities in content. '
            'Uses the simplest thing I could think of that might work, and '
            'is therefore somewhat slow.'
        )
        bobsim.add_argument(
            'text_one', type=str, help='The first play text file.'
        )
        bobsim.add_argument(
            'text_two', type=str, help='The second play text file.'
        )
        bobsim.set_defaults(command=self.bobsim)

        self.args = parser.parse_args()

    def __call__(self, *args, **kwargs):
        self.args.command(*args, **kwargs)

    def cwords(self, *args, **kwargs):
        texts = self.args.texts
        lines = [loadlines(t, character_allcaps_split) for t in texts]
        plays = [Play(ln) for ln in lines]
        wcs = [CharacterWordCount(p) for p in plays]
        char = self.args.character

        for t, wc in zip(texts, wcs):
            print
            print '{}:'.format(t),
            wc(None if char == 'all' else char)

    def diff(self):
        char = self.args.character
        path_a = self.args.text_one
        path_b = self.args.text_two
        lines_a = loadlines(path_a, character_allcaps_split)
        lines_b = loadlines(path_b, character_allcaps_split)
        play_a = Play(lines_a)
        play_b = Play(lines_b)
        words_a = play_a.regular_text(char)
        words_b = play_b.regular_text(char)
        # print words_a
        # print "__________________________________________"
        # print words_b
        s = SequenceMatcher(a=words_a,
                            b=words_b)

        msg = 'Ratio of similarity betwteen {} and {}'
        msg += ':' if char is None else ' for character {}:'.format(char)
        print msg.format(path_a, path_b)
        print '  {}'.format(s.ratio())
        print
        print '(Where T is the total number of elements in both sequences, '
        print ' and M is the number of matches, this is 2.0*M / T. Note '
        print ' that this is 1.0 if the sequences are identical, and 0.0 '
        print ' if they have nothing in common. '
        print '                --Python difflib documentation)'
        print

        msg = {
            'replace': '{n}. Replace\n\n{text_a}\n\n with \n\n{text_b}\n\n',
            'insert': '{n}. Insert\n\n{text_b}\n\n',
            'delete': '{n}. Delete\n\n{text_a}\n\n',
            'equal': '{n}. Preserve\n\n{text_a}\n\n',
        }

        for n, op in enumerate(s.get_opcodes()):
            op, s1, e1, s2, e2 = op
            print msg[op].format(n=n,
                                 text_a=words_a[s1:e1],
                                 text_b=words_b[s2:e2])

    def bobsim(self):
        path_a = self.args.text_one
        path_b = self.args.text_two
        lines_a = loadlines(path_a, character_allcaps_split)
        lines_b = loadlines(path_b, character_allcaps_split)
        lines_a = [l for l in lines_a if len(l.words) > 74]
        lines_b = [l for l in lines_b if len(l.words) > 74]
        bobs_a = [bag_of_ngrams(l.words) for l in lines_a]
        bobs_b = [bag_of_ngrams(l.words) for l in lines_b]

        vocab = set()
        for bob in bobs_a:
            vocab |= set(bob)

        for bob in bobs_b:
            vocab |= set(bob)

        vectors_a = [[bob[bg] for bg in vocab] for bob in bobs_a]
        vectors_b = [[bob[bg] for bg in vocab] for bob in bobs_b]
        rows = []
        for v in vectors_a:
            row = [cosine_sim(v, u) for u in vectors_b]
            rows.append(row)
            for col in row:
                print '{:0.1f}'.format(col),
            print

        for i, (line_a, row) in enumerate(zip(lines_a, rows)):
            for j, csim in enumerate(row):
                if csim > 0.1:
                    line_b = lines_b[j]
                    print "__________________________"
                    print "Similar pair:"
                    print
                    print line_a.character
                    print line_a.text
                    print
                    print line_b.character
                    print line_b.text
                    print

                    sm = SequenceMatcher(line_a.words, line_b.words)
                    print 'Similarity: {}'.format(sm.ratio())
                    print

                    print "____________"
                    print "Edits:"
                    df = Differ()
                    for diffline in df.compare(line_a.text.splitlines(),
                                               line_b.text.splitlines()):
                        print diffline
                    print
                    print

    def bobsim_sum(self):
        """This was interesting because it picked out one line as especially
        distinctive -- as especially similar to many other lines in the play.
        Hunch: follows an exponential distribution; a few lines are very
        similar to most lines and the value falls away quickly. Most
        similar line is interesting somehow!
        """
        path = self.args.text
        lines = loadlines(path, character_allcaps_split)
        lines = [l for l in lines if len(l.words) > 74]
        bobs = [bag_of_ngrams(l.words) for l in lines]

        vocab = set()
        for bob in bobs:
            vocab |= set(bob)

        vectors = [[bob[bg] for bg in vocab] for bob in bobs]
        rowsums = []
        for v in vectors:
            row = [cosine_sim(v, u) for u in vectors]
            for col in row:
                print '{:0.1f}'.format(col),
            rowsums.append(sum(row))
            print
        print lines[max(range(len(rowsums)), key=rowsums.__getitem__)]

if __name__ == '__main__':
    cmd = Commands()
    cmd()
