import os

from file_read_backwards import FileReadBackwards


def truncateXMLDump(filename: str) -> None:
    """Removes incomplete <page> elements from the end of XML dump files"""

    with FileReadBackwards(filename, encoding="utf-8") as frb:
        incomplete_segment: str = ""
        xml_line: str = frb.readline()
        while xml_line and "</page>" not in xml_line:
            incomplete_segment += xml_line
            xml_line = frb.readline()
    incomplete_segment_size = len(incomplete_segment.encode("utf-8"))
    file_size = os.path.getsize(filename)
    with open(filename, "r+", encoding="utf-8") as fh:
        fh.truncate(file_size - incomplete_segment_size)
