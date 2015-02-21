from pmetro.files import read_all_lines


class IniReader(object):
    def __init__(self):
        self.lines = []
        self.position = None

    def open(self, path):
        self.lines = read_all_lines(path)
        self.position = 0

    def section(self, section):
        index = 0
        pattern = '[' + section + ']'
        while index < len(self.lines):
            if self.lines[index].strip().lower() == pattern.lower():
                self.position = index
                return
            index += 1
        raise 'No section ' + section + ' found'

    def read(self):
        if self.position is None:
            self.position = 0
        else:
            self.position += 1

        if self.position >= len(self.lines):
            return False

        line = self.lines[self.position].strip()
        if line.startswith('[') and line.endswith(']'):
            return False

        return True

    def name(self):
        return self.lines[self.position].strip().lower().split('=')[0]

    def value(self):
        return self.lines[self.position].strip().split('=')[1]


