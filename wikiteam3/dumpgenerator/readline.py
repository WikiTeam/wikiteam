import os


def reverse_readline(filename, buf_size=8192, truncate=False):
    """a generator that returns the lines of a file in reverse order"""
    # Original code by srohde, abdus_salam: cc by-sa 3.0
    # http://stackoverflow.com/a/23646049/718903
    with open(filename, "r+") as fh:
        segment = None
        offset = 0
        fh.seek(0, os.SEEK_END)
        total_size = remaining_size = fh.tell()
        while remaining_size > 0:
            offset = min(total_size, offset + buf_size)
            fh.seek(-offset, os.SEEK_END)
            buffer = fh.read(min(remaining_size, buf_size))
            remaining_size -= buf_size
            lines = buffer.split("\n")
            # the first line of the buffer is probably not a complete line so
            # we'll save it and append it to the last line of the next buffer
            # we read
            if segment is not None:
                # if the previous chunk starts right from the beginning of line
                # do not concat the segment to the last line of new chunk
                # instead, yield the segment first
                if buffer[-1] != "\n":
                    lines[-1] += segment
                else:
                    if truncate and "</page>" in segment:
                        pages = buffer.split("</page>")
                        fh.seek(-offset + buf_size - len(pages[-1]), os.SEEK_END)
                        fh.truncate
                        raise StopIteration
                    else:
                        yield segment
            segment = lines[0]
            for index in range(len(lines) - 1, 0, -1):
                if truncate and "</page>" in segment:
                    pages = buffer.split("</page>")
                    fh.seek(-offset - len(pages[-1]), os.SEEK_END)
                    fh.truncate
                    raise StopIteration
                else:
                    yield lines[index]
        yield segment
