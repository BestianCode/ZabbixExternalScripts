#!/usr/bin/env python3

#**************************** AWS cloud Monitor ******************************
#*
#*  Copyright (c) 2018, Oleg Smirnov <oleg.a.smirnov@gmail.com>
#*  All rights reserved.
#*
#*  Redistribution and use in source and binary forms, with or without
#*  modification, are permitted provided that the following conditions
#*  are met:
#*  1. Redistributions of source code must retain the above copyright
#*     notice, this list of conditions and the following disclaimer.
#*  2. Redistributions in binary form must reproduce the above copyright
#*     notice, this list of conditions and the following disclaimer in the
#*     documentation and/or other materials provided with the distribution.
#*
#*  THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
#*  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#*  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#*  ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
#*  FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
#*  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
#*  OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
#*  HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#*  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
#*  OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#*  SUCH DAMAGE.
#*
#*****************************************************************************

import socket
import ssl
import datetime
import getopt
import sys
import json

dateFmt = r'%b %d %H:%M:%S %Y %Z'

appVersion = "2018.12.10.02"

def about(exitCode=0,additionalMessage=""):
    print(" \
\n \
Copyright (c) 2018, Oleg Smirnov <oleg.a.smirnov@gmail.com>.\n \
Simplified BSD License or FreeBSD License.\n \
v",appVersion,"\n \
\n \
"+sys.argv[0]+" -d <dnsname> [-p port]\n \
\n \
    -d - DNS Name of the server\n \
    -p - port number\n \
\n \
",sep='')
    if additionalMessage!="":
        print("\
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n\n\
",additionalMessage,"\n\n\
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n",sep='',end='')
    exit(exitCode)

try:
    opts, args = getopt.getopt(sys.argv[1:],"hd:p:")
except getopt.GetoptError:
    about(2)

for opt, arg in opts:
    if opt == '-h':
        about(0)
    elif opt == "-d":
        xhost = arg
    elif opt == "-p":
        xport = arg

try:
    if xhost == "":
        about(2)
    else:
        host=xhost
except:
    about(2)

try:
    if int(xport)>0 and int(xport)<65535:
        port=int(xport)
    else:
        port=443
except:
    port=443

context = ssl.create_default_context()
conn = context.wrap_socket(
    socket.socket(socket.AF_INET),
    server_hostname=host,
)

conn.settimeout(5.0)
conn.connect((host, port))

ssl_info = conn.getpeercert()

rDesc={}
dateExp=datetime.datetime.strptime(ssl_info['notAfter'], dateFmt).timestamp()
dateNow=datetime.datetime.utcnow().timestamp()
rDesc["days"]=int((dateExp-dateNow)/60/60/24)
rDesc["date"]=ssl_info['notAfter']
rDesc["serial"]=ssl_info['serialNumber']
print(json.dumps(rDesc, indent="\t"))
