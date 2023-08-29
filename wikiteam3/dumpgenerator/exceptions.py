class PageMissingError(Exception):
    def __init__(self, title, xml):
        self.title = title
        self.xml = xml

    def __str__(self):
        return f"page '{self.title}' not found"


class ExportAbortedError(Exception):
    def __init__(self, index):
        self.index = index

    def __str__(self):
        return f"Export from '{self.index}' did not return anything."


class FileSizeError(Exception):
    def __init__(self, file, size):
        self.file = file
        self.size = size

    def __str__(self):
        return f"File '{self.file}' size is not match '{self.size}'."


class FileSha1Error(Exception):
    def __init__(self, file, sha1):
        self.file = file
        self.sha1 = sha1

    def __str__(self):
        return f"File '{self.file}' sha1 is not match '{self.sha1}'."
