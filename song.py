import urllib

class Song(object):
    def dump_info(self):
        print self.title, self.location

def decrypt_location(encrypted):
    output = ''

    # decryption method obtained from internet
    # characters of the URL is listed in a table vertically
    # and the encoding result is read out horzontally

    # first part is the number of rows
    i = 0
    while encrypted[i].isdigit():
        i += 1
    rows = int(encrypted[:i])
    encrypted = encrypted[i:]
    total_len = len(encrypted)

    # looks like this:

    # h******************** ^
    # t******************** | final_col_len
    # t******************** v
    # p*******************
    # %*******************
    # <-   min_row_len  ->

    r = 0
    c = 0
    pos = 0
    min_row_len = total_len / rows
    final_col_len = total_len % rows
    for x in xrange(total_len):
        output += encrypted[pos]
        if r == rows - 1:
            # last row reached, reset to first row
            r = 0
            c += 1
            pos = c
        else:
            # move to next row
            pos += min_row_len
            if r < final_col_len:
                pos += 1
            r += 1

    # why 0 is replaced by ^.....
    return urllib.unquote(output).replace('^', '0')
