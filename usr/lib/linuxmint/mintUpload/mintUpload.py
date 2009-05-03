#!/usr/bin/env python

#   Clement Lefebvre <root@linuxmint.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; Version 2
# of the License.
 
try:
    import os
    from mintUploadCore import *
except:
    print "You do not have all the dependencies!"
    sys.exit(1)

# i18n
gettext.install("messages", "/usr/lib/linuxmint/mintUpload/locale")

def cliUpload(servicename, filename):
    services = read_services()
    for service in services:
        if service['name'] == servicename:

            # Check there is enough space on the service, ignore threading
            filesize = os.path.getsize(filename)
            checker = mintSpaceChecker(service, filesize)
            proceed = checker.run()

            if proceed:
                # Upload
                uploader = mintUploader(service, filename)
                uploader.start()
            else:
                raise CustomError(_("Upload failed."))

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print "need a file to upload!"
        exit(1)

    elif sys.argv[1] == "--version":
        print "mintupload: %s" % commands.getoutput("mint-apt-version mintupload 2> /dev/null")
        exit(0)
    elif sys.argv[1] in ["-h","--help"]:
        print """Usage: mintupload.py path/to/filename"""
        print """Usage: mintupload.py -cli SERVICE path/to/filename"""
        exit(0)
    elif sys.argv[1] == "-cli":
        if len(sys.argv) == 4:
            cliUpload(sys.argv[2], sys.argv[3])
        else:
            print """Usage: mintupload.py -cli SERVICE path/to/filename"""

    elif len(sys.argv) > 2:
        print "too many files! using only the first!"

    from gtkUpload import *
    mainwin = mintUploadWindow(sys.argv[1])
    gtk.main()

