import codecs
import datetime


class LogLevel(object):
    Debug = 0
    Info = 1
    Warning = 2
    Error = 3
    Message = 4


class BaseLog(object):
    def __init__(self, level=LogLevel.Debug):
        self.level = level

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def write(self, message, level=LogLevel.Debug):
        pass

    def info(self, message):
        self.write(message, LogLevel.Info)

    def error(self, message):
        self.write(message, LogLevel.Error)

    def warning(self, message):
        self.write(message, LogLevel.Warning)

    def debug(self, message):
        self.write(message, LogLevel.Debug)

    def message(self, message):
        self.write(message, LogLevel.Message)

    @staticmethod
    def log_level_text(level):
        return {
            LogLevel.Debug: 'Debug',
            LogLevel.Info: 'Info',
            LogLevel.Warning: 'Warning',
            LogLevel.Error: 'Error',
            LogLevel.Message: 'Message'
        }[level]


class EmptyLog(BaseLog):
    pass


class CompositeLog(BaseLog):
    def __init__(self, loggers=None):
        super(CompositeLog, self).__init__(LogLevel.Debug)
        self.loggers = loggers

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        for l in self.loggers:
            l.__exit__(exc_type, exc_val, exc_tb)

    def write(self, message, level=LogLevel.Debug):
        for l in self.loggers:
            l.write(message, level)


class ConsoleLog(BaseLog):
    def __init__(self, level=LogLevel.Debug):
        super(ConsoleLog, self).__init__(level)

    def write(self, message, level=LogLevel.Debug):
        if level >= self.level:
            print(message)


class FileLog(BaseLog):
    def __init__(self, file_path='', level=LogLevel.Debug):
        super(FileLog, self).__init__(level)
        self.file = codecs.open(file_path, 'a', encoding='utf-8')

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file is not None:
            self.file.close()

    def write(self, message, level=LogLevel.Debug):
        if level >= self.level:
            self.file.write('[%s][%s] %s\n' % (
                datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S.%f'), BaseLog.log_level_text(level), message))
            self.file.flush()

