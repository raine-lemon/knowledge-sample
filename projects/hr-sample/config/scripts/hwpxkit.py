# -*- coding: utf-8 -*-
"""최소 OWPML HWPX 작성기. hwp-hwpx-parser가 읽는 구조(META-INF/manifest.xml +
Contents/section0.xml, <hp:p>/<hp:t>)를 만족한다. 한컴오피스 바이트 호환은 목표가 아니다."""
import os, zipfile

HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"

def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def write(path, lines):
    body = "".join(
        "<hp:p><hp:run><hp:t>%s</hp:t></hp:run></hp:p>" % (_esc(l) if l else "")
        for l in lines)
    section = ('<?xml version="1.0" encoding="UTF-8"?>'
               '<hp:sec xmlns:hp="%s">%s</hp:sec>' % (HP, body))
    manifest = ('<?xml version="1.0" encoding="UTF-8"?>'
        '<manifest xmlns="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0">'
        '<file-entry full-path="/" media-type="application/hwp+zip"/>'
        '<file-entry full-path="Contents/header.xml" media-type="application/xml"/>'
        '<file-entry full-path="Contents/section0.xml" media-type="application/xml"/>'
        '</manifest>')
    header = ('<?xml version="1.0" encoding="UTF-8"?>'
        '<hh:head xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" secCnt="1"/>')
    version = ('<?xml version="1.0" encoding="UTF-8"?>'
        '<hv:HCFVersion xmlns:hv="http://www.hancom.co.kr/hwpml/2011/version" '
        'tagetApplication="WORDPROCESSOR" major="5" minor="1" micro="0" buildNumber="0"/>')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("mimetype", "application/hwp+zip")
        z.writestr("version.xml", version)
        z.writestr("META-INF/manifest.xml", manifest)
        z.writestr("Contents/header.xml", header)
        z.writestr("Contents/section0.xml", section)
    return os.path.getsize(path)
