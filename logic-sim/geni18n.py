# -*- coding: utf-8 -*-
"""
This will generate the .pot and .mo files for the application domain and
languages defined below.

The .po and .mo files are placed as per convention in

"appfolder/locale/lang/LC_MESSAGES"

The .pot file is placed in the locale folder.

This script or something similar should be added to your build process.

The actual translation work is normally done using a tool like poEdit or
similar, it allows you to generate a particular language catalog from the .pot
file or to use the .pot to merge new translations into an existing language
catalog.

"""

import app_const as appC

# we remove English as source code strings are in English
supportedLang = []
for l in appC.supLang:
    if l != u"en":
        supportedLang.append(l)

import os
import sys
import subprocess

appFolder = os.getcwd()

# setup some stuff to get at Python I18N tools/utilities

pyExe = '/usr/bin/python'
#pyFolder = os.path.split(pyExe)[0]
#pyToolsFolder = '~/gf2/i18n/cpython/Tools/'
#pyI18nFolder = os.path.join(pyToolsFolder, 'i18n')
pyGettext = '/usr/bin/pygettext.py'
pyMsgfmt = '/usr/bin/msgfmt'
outFolder = os.path.join(appFolder, 'locale')

# build command for pygettext
gtOptions = '-a -d %s -o %s.pot -p %s %s'
tCmd = pyExe + ' ' + pyGettext + ' ' + (gtOptions % (appC.langDomain,
                                                     appC.langDomain,
                                                     outFolder,
                                                     appFolder))
print ("Generating the .pot file")
print ("cmd: %s" % tCmd)
rCode = os.system(tCmd)
print ("return code: %s\n\n" % rCode)

for tLang in supportedLang:
    # build command for msgfmt
    langDir = os.path.join(appFolder, ('locale/%s/LC_MESSAGES' % tLang))
    poFile = os.path.join(langDir, appC.langDomain + '.po')
    moFile = os.path.join(langDir, appC.langDomain + '.mo')
    tCmd = pyMsgfmt + ' ' + poFile + ' -o ' + moFile
    
    print ("Generating the .mo file")
    print ("cmd: %s" % tCmd)
    rCode = os.system(tCmd)
    print ("return code: %s\n\n" % rCode)
