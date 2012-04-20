#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2011-2012 WikiTeam
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# http://archive.org/help/abouts3.txt
# https://wiki.archive.org/twiki/bin/view/Main/IAS3BulkUploader
# http://en.ecgpedia.org/api.php?action=query&meta=siteinfo&siprop=rightsinfo

import os
import re
import subprocess
import urllib

"""
log = subprocess.check_output(['curl', '--location', 
    '--header', "'x-amz-auto-make-bucket:1",
    '--header', "'x-archive-queue-derive:0",
    '--header', "'x-archive-size-hint:9638436173'", 
    '--header', "'authorization: LOW accesskey:secretkey'",
    '--header', "'x-archive-meta-mediatype:web'",
    '--header', "'x-archive-meta-collection:opensource'",
    '--header', "'x-archive-meta-title:Wiki - ECGpedia'",
    '--header', "'x-archive-meta-description:<a href=\"http://en.ecgpedia.org/\" rel=\"nofollow\">ECGpedia,</a>: a free electrocardiography (ECG) tutorial and textbook to which anyone can contribute, designed for medical professionals such as cardiac care nurses and physicians. Dumped with <a href=\"http://code.google.com/p/wikiteam/\" rel=\"nofollow\">WikiTeam</a> tool.'"
    '--header', "'x-archive-meta-subject:ecg; ECGpedia; wiki; wikiteam; MediaWiki'",
    '--header', "'x-archive-meta-licenseurl:http://creativecommons.org/licenses/by-nc-sa/3.0/'",
    '--header', "'x-archive-meta-rights:http://en.ecgpedia.org/wiki/Frequently_Asked_Questions'",
    '--header', "'x-archive-meta-originalurl:http://en.ecgpedia.org/api.php'",
    '--upload-file', "/home/.../ArchiveTeam/WikiTeam/enecgpediaorg-20120419-wikidump.7z",
    "http://s3.us.archive.org/wiki-en.ecgpedia.org/enecgpediaorg-20120419-wikidump.7z"
    ])
"""

def upload(f):
    print f

wikis = []
def main():
    for dirname, dirnames, filenames in os.walk('.'):
        if dirname == '.':
            for f in filenames:
                if f.endswith('-wikidump.7z') or f.endswith('-history.xml.7z'):
                    upload(f)
            break

if __name__ == "__main__":
    main()
