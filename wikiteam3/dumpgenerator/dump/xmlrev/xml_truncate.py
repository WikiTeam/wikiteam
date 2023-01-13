import os

from file_read_backwards import FileReadBackwards


def endsWithNewlines(filename: str) -> int:
    """Returns the number of newlines at the end of file"""

    with FileReadBackwards(filename, encoding="utf-8") as frb:
        newlines = 0
        while frb.readline() == "":
            newlines += 1
    return newlines


def addNewline(filename: str) -> None:
    """Adds a newline to the end of file"""

    print(f"Adding newline to end of {filename}")
    with open(filename, "a", encoding="utf-8") as f:
        f.write("\n")


def truncateXMLDump(filename: str) -> None:
    """Removes incomplete <page> elements from the end of XML dump files"""

    with FileReadBackwards(filename, encoding="utf-8") as frb:
        incomplete_segment: str = ""
        xml_line: str = frb.readline()
        while xml_line and "</title>" not in xml_line:
            incomplete_segment += xml_line
            xml_line = frb.readline()
        while xml_line and "</page>" not in xml_line:
            incomplete_segment += xml_line
            xml_line = frb.readline()
    incomplete_segment_size = len(incomplete_segment.encode("utf-8"))
    file_size = os.path.getsize(filename)
    if file_size > incomplete_segment_size:
        with open(filename, "r+", encoding="utf-8") as fh:
            fh.truncate(file_size - incomplete_segment_size)
    else:
        print(
            'len(incomplete_segment.encode("utf-8")) returned '
            + str(incomplete_segment_size)
            + ", while os.path.getsize(filename) returned "
            + str(file_size)
            + ", so fh.truncate() would be fh.truncate("
            + str(file_size - incomplete_segment_size)
            + "), which would be illegal. Something is seriously wrong here!"
        )

    # add newline to prevent `</page> <page>` in one line
    if endsWithNewlines(filename) == 0:
        addNewline(filename)
    elif endsWithNewlines(filename) > 1:
        print(
            f"WARNING: {filename} has {endsWithNewlines(filename)} newlines"
        )
