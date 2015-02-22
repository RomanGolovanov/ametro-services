
class DelaysString(object):
    def __init__(self, text):
        self.text = str(text)
        self.pos = 0
        if text is None:
            self.len = 0
        else:
            self.len = len(text)

    def begin_bracket(self):
        return self.text is not None and self.pos < self.len and self.text[self.pos] == '('

    def next_block(self):
        if self.text is None:
            return None

        if self.begin_bracket():
            idx = self.text.find(')', self.pos)
        else:
            idx = self.pos

        next_comma = self.text.find(',', idx)
        if next_comma!= -1:
            block = self.text[self.pos: next_comma]
            self.pos = next_comma + 1
        else:
            block = self.text[self.pos:]
            self.pos = self.len

        return block

    def next(self):
        return float(self.next_block())

    def next_bracket(self):
        if self.text is None:
            return None
        delays = []
        for p in self.next_block()[1:-1].split(','):
            fp = float(p)
            minutes = int(fp)
            seconds = int((fp - minutes) * 100)
            delays.append(minutes * 60 + seconds)
        return


class StationsString:
    def __init__(self, text):
        self.text = str(text)
        self.len = len(text)
        self.separators = ',()'
        self.pos = 0
        self.next_separator = ''
        self.reset()

    def reset(self):
        self.pos = 0
        self.skip_to_content()

    def at_next(self):
        if self.pos < self.len:
            return self.text[self.pos: self.pos + 1]
        else:
            return None

    def has_next(self):
        try:
            current = self.pos
            self.skip_to_content()
            return not self.__eof()
        finally:
            self.pos = current

    def __eof(self):
        return self.pos >= self.len

    def next(self):
        self.skip_to_content()
        if self.__eof():
            return ''
        current = self.pos
        symbol = None
        quotes = False
        while current < self.len:
            symbol = self.text[current:current + 1]
            if not (symbol not in self.separators or quotes ):
                break

            if symbol == '"':
                quotes = not quotes
            current += 1

        if symbol is None:
            end = current - 1
        else:
            end = current

        self.next_separator = symbol
        txt = self.text[self.pos: end]
        self.pos = end
        return txt.strip('"')


    def skip_to_content(self):
        symbol = symbol_next = self.at_next()
        while self.pos < self.len and symbol in self.separators:
            if symbol == '(':
                self.pos += 1
                return

            self.pos += 1
            symbol_next = self.at_next()

            if symbol == ',' and symbol_next != '(':
                return
            symbol = symbol_next
