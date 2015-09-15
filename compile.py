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

base = ""
tmp = []

def readfile(filename):
    try:
        f = open(filename, 'r')
        content = f.read()
        f.close()
        return content
    except:
        print "ERR: Couldn't find " + filename
        return None

def img_compile(filename):
    try:
        mime = magic.from_file(filename, mime=True)
        data = base64.b64encode(readfile(filename))
        return "data:%s;base64,%s" % (mime, data)
    except Exception as inst:
        print "ERR: %s (%s)" % (inst, type(inst))
        return None

def html_css_image(tag):
    if len(tmp) > 0:
        path = tmp[0]
    else:
        path = base

    src = tag.group(1)
    if not "://" in src:
        src = img_compile(path + src)

    if src is None:
        src = tag.group(1)

    return 'url("%s")' % src

def html_css_image2(tag):
    if len(tmp) > 0:
        path = tmp[0]
    else:
        path = base

    src = tag.group(1)
    if not "://" in src:
        src = img_compile(path + src)

    if src is None:
        src = tag.group(1)

    return 'url(%s)' % src

def html_process_css(data, path):
    tmp.append(path)
    result = re.sub(r'url\("([^"\?\#]+)"\)', html_css_image, data)
    result = re.sub(r'url\(([^"\?\#\)]+)\)', html_css_image2, data)
    del tmp[:]
    return result


def html_embed_css(tag):
    # Obtain the filename
    p = re.compile('href="([^"]+)"')
    m = p.search(tag)
    if m and not "://" in m.group(1):
        content = readfile(base + m.group(1))
        if content:
            tmp = os.path.dirname(base + m.group(1)) + "/"
            content = html_process_css(content, tmp)
            return '<style type="text/css">' + content + '</style>'
        else:
            return tag
#    else:
#        print "No match for " + tag
    return tag

def html_embed_script(tag):
    # Obtain the filename
    p = re.compile('src="([^"]+)"')
    m = p.search(tag)
    if m and not "://" in m.group(1):
        content = readfile(base + m.group(1))
        if content:
            return '<script type="text/javascript">' + content
        else:
            return tag
#    else:
#        print "No match for " + tag
    return tag

def html_img_src(m):
    src = m.group(1)
    if not "://" in src:
        src = img_compile(base + src)

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
    elif tag[1:5] == "link":
        tag = html_embed_css(tag)
    elif tag[1:7] == "script":
        tag = html_embed_script(tag)
    #else:
        #print 'Ignoring "%s"' % tag
    return tag

def html_compile(filename):
    content = readfile(filename)
    content = re.sub(r'<[^>]+>', html_translate, content)
    return content


if len(sys.argv) is not 3:
    print "Usage: %s <input html> <output html>" % os.path.basename(sys.argv[0])
    sys.exit(1)

infile = sys.argv[1]
outfile = sys.argv[2]

print "Parsing %s into %s" % (infile, outfile)

base = os.path.dirname(infile)
if base is "":
    base = "."
base += "/"
data = html_compile(infile)

o = open(outfile, 'w')
o.write(data)
o.close()
