#!/usr/bin/env python
#
# Inline all external CSS/JS/Images dependencies into the HTML file
# Copyright (C) 2015 Henric Andersson (henric@sensenet.nu)
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
import re
import sys
import os
import magic
import base64
import logging
import argparse

""" Parse command line """
parser = argparse.ArgumentParser(description="HTMLcompiler - Keeping it all in one place", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('input', metavar='IN', help="Input file to use as base for compilation")
parser.add_argument('output', metavar='OUT', help="The resulting file containing the compiled HTML")
parser.add_argument('-t', '--trace', dest='trace',action='store_true',default=False, help="Show what the compiler is doing")
parser.add_argument('-n', '--noclean', dest='noclean',action='store_true',default=False, help="Do not clean up filenames (see README.md)")
cmdline = parser.parse_args()

""" Setup logging """
logging.getLogger('').handlers = []
dbg = logging.INFO
if cmdline.trace:
    dbg = logging.DEBUG
#logging.basicConfig(level=dbg, format='%(asctime)s - %(filename)s@%(lineno)d - %(levelname)s - %(message)s')
logging.basicConfig(level=dbg, format='%(levelname)7s: %(message)s')

""" Init needed variables """
base = ""
tmp = []
goodmagic = True

# Two libraries, one magic, detect which
if not hasattr(magic, 'from_file'):
    goodmagic = False

def cleanup_filename(filename):
    # Very odd, some servers send %252F instead of %2F for forwardslash
    # we'll just compensate here (wget produces files likes those)
    filename = filename.replace("%252F", "%2F")
    filename = filename.replace("&amp;", "&")
    # Remove ending hash
    filename = re.sub(r'#.*$', '', filename)
    return filename

def readfile(filename):
    try:
        f = open(filename, 'r')
        content = f.read()
        f.close()
        return content
    except:
        logging.warn("File not found " + filename)
        if cmdline.noclean and os.path.isfile(cleanup_filename(filename)):
            logging.info("File was found after cleaning. Maybe remove -n/--noclean option?")
        return None

def img_compile(filename):
    if not cmdline.noclean:
        filename = cleanup_filename(filename)

    try:
        mime = None
        if goodmagic:
            mime = magic.from_file(filename, mime=True)
        else:
            m = magic.open(magic.MIME_TYPE)
            m.load()
            mime = m.file(filename)
            m.close()

        data = readfile(filename)
        if data is not None:
            data = base64.b64encode(readfile(filename))
            return "data:%s;base64,%s" % (mime, data)
        else:
            return filename
    except Exception as inst:
        logging.error("%s (%s)" % (inst, type(inst)))
        return None

def html_css_image(tag):
    if len(tmp) > 0:
        path = tmp[0]
    else:
        path = base

    src = tag.group(1)
    enclose=""
    if src[0] == '"' or src[0] == "'":
        enclose = src[0]
        src = src[1:-1]
    if not "://" in src and src[:5] != "data:":
        logging.debug('Inline   url("%s")' % src)
        src = img_compile(path + src)
    elif src[:5] == "data:":
        logging.debug('Embedded url("%s")' % re.sub(r';.+$', '', src))
    else:
        logging.debug('External url("%s")' % src)

    if src is None:
        src = tag.group(1)

    return 'url(%s%s%s)' % (enclose, src, enclose)

def html_process_css(data, path):
    tmp.append(path)
    result = re.sub(r'url\(([^\)]+)\)', html_css_image, data)
    del tmp[:]
    return result


def html_embed_css(tag):
    # Obtain the filename
    p1 = re.compile('href="([^"]+)"')
    p2 = re.compile('href=\'([^\']+)\'')
    m1 = p1.search(tag)
    m2 = p2.search(tag)
    m = None
    if m1: m = m1
    if m2: m = m2

    if m and not "://" in m.group(1):
        content = readfile(base + m.group(1))
        if content:
            logging.debug('Inline   <link href="%s">' % m.group(1))
            tmp = os.path.dirname(base + m.group(1)) + "/"
            content = html_process_css(content, tmp)
            return '<style type="text/css">' + content + '</style>'
        else:
            logging.debug('External <link href="%s">' % m.group(1))
            return tag
    return tag

def html_embed_script(tag):
    # Obtain the filename
    p1 = re.compile('src="([^"]+)"')
    p2 = re.compile('src=\'([^\']+)\'')
    m1 = p1.search(tag)
    m2 = p2.search(tag)
    m = None
    if m1: m = m1
    if m2: m = m2

    if m and not "://" in m.group(1):
        content = readfile(base + m.group(1))
        if content:
            logging.debug('Inline   <script src="%s">' % m.group(1))
            return '<script type="text/javascript">' + content
        else:
            logging.debug('External <script src="%s">' % m.group(1))
            return tag
    return tag

def html_img_src(m):
    src = m.group(1)
    if not "://" in src and src[:5] != "data:":
        logging.debug('Inline   <img src="%s">' % src)
        src = img_compile(base + src)
    else:
        logging.debug('External <img src="%s">' % src)

    if src is None:
        src = m.group(1)

    return 'src="' + src + '"'

def html_translate(m):
    tag = m.group()
    # Skip end-tags
    if tag[1] == '/':
        return m.group()

    # See if any of these contains a src="" construct...
    if tag[1:4] == "img":
        tag = re.sub(r'src="([^"]+)"', html_img_src, tag)
    elif tag[1:5] == "link" and "stylesheet" in tag:
        tag = html_embed_css(tag)
    elif tag[1:7] == "script":
        tag = html_embed_script(tag)
    return tag

def html_process_inline_css_tag(m):
    attr = m.group(1)
    data = m.group(2)
    content = html_process_css(data, base)
    return '<style%s>%s</style>' % (attr, content)

def html_process_inline_css_attr(m):
    attr = m.group(1)
    data = m.group(2)
    content = html_process_css(data, base)
    #print "Processed: " + content
    return '<%s style="%s"' % (attr, content)


def html_compile(filename):
    content = readfile(filename)
    # Special case, we need to deal with already inlined CSS
    content = re.sub(r'<style([^>]*)>([^<]*)</style>', html_process_inline_css_tag, content)

    # Also, don't forget the style attribute :-P
    content = re.sub(r'<(.*) style="([^"]+)"', html_process_inline_css_attr, content)
    content = re.sub(r'<(.*) style=\'([^\']+)\'', html_process_inline_css_attr, content)

    # Now, do the rest...
    content = re.sub(r'<[^>]+>', html_translate, content)
    return content

infile = cmdline.input
outfile = cmdline.output

if not os.path.exists(infile):
    logging.error("File %s doesn't exist" % infile)
    sys.exit(2)
if not os.path.isfile(infile):
    logging.error("File %s is not a file" % infile)
    sys.exit(3)

logging.info("Parsing %s into %s" % (infile, outfile))

base = os.path.dirname(infile)
if base is "":
    base = "."
base += "/"
data = html_compile(infile)

o = open(outfile, 'w')
o.write(data)
o.close()

logging.info("Complete!")