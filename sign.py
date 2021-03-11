#!/usr/bin/env python3

#Dependencies:
from pdfrw import PdfReader, PdfWriter, PageMerge
from bs4 import BeautifulSoup
# pdftotext: apt install poppler-utils

import os, sys, subprocess

class LinePos:
    """ Find line position in pdf of instructor.cz certificate. """
    def __init__(self, filename):
        soup = BeautifulSoup(subprocess.check_output(['pdftotext', '-bbox', filename, '-']), 'html.parser')
        e = soup.select('page')
        self.w, self.h = [ float(e[0][k]) for k in ("width", "height") ]
        for w in soup.select('word'):
            if '..........' in w.text:
                self.l, self.r, self.t, self.b = [ float(w[k]) for k in
                ('xmin', 'xmax', 'ymin', 'ymax') ]


class SigPos:
    def __init__(self, sigpage):
        self.l, self.b, self.r, self.t = [ float(x) for x in sigpage.MediaBox ]


def add_signature(certname, signame, outname, under = True):
    if under not in (None, False, 0, '0', 'no', 'false', "False", ''):
        under = True
    else:
        under = False
    l = LinePos(certname)

    sigp = PdfReader(signame).pages[0]
    cert = PdfReader(certname)

    s = SigPos(sigp)

    m = PageMerge(cert.pages[0]).add(sigp ,prepend=under)
    msig = m[not under]
    msig.x = (l.r + l.l)/2 - (s.r + s.l)/2
    msig.y = l.h - l.t
    m.render()

    PdfWriter(outname, trailer=cert).write()

if 4 <= len(sys.argv) <= 5:
    add_signature(sys.argv[1], sys.argv[2], sys.argv[3]+sys.argv[1], *sys.argv[4:])
else:
    print(
"""Usage: %s certificate.pdf signature.pdf output_prefix [no]

If fourth parameter is "no" then signature is rendered over text,
instead of under text. (It should be blank space anyway, under
is slightly better for non-transparent images.)""")
    sys.exit(1)
