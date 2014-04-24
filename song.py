import urllib

class Song(object):
    def dump_info(self):
        print self.title, self.location

def decrypt_location(encrypted):
    output = ''

    i = 0
    while encrypted[i].isdigit():
        i += 1
    rows = int(encrypted[:i])
    encrypted = encrypted[i:]
    total_len = len(encrypted)

    r = 0
    c = 0
    pos = 0
    min_row_len = total_len / rows
    final_col_len = total_len % rows
    for x in xrange(total_len):
        output += encrypted[pos]
        if r == rows - 1:
            r = 0
            c += 1
            pos = c
        else:
            pos += min_row_len
            if r < final_col_len:
                pos += 1
            r += 1

    return urllib.unquote(output).replace('^', '0')

