#!/usr/bin/env python

import socket
import re
import sys
import signal

__version__ = '20090821'

regex_ip = re.compile(r'(?P<ip>(\d{1,3}\.){3}\d{1,3})')

def gracexit(signum, frame):
	sys.exit()
signal.signal(signal.SIGINT, gracexit)

def Usage():
	print """ipconv.py version %s
Usage:
	ipconv.py [-o] appui.conf
	tail -f appui.log | ipconv.py [-o]
	(-o means only match)"""%(__version__)
	return -2

def ipsum(fp,verbose = False):
	while True:
		line = fp.readline()
		if line == '':
			break
		ip_in_line = [x[0] for x in regex_ip.findall(line)]
		if ip_in_line:
			for ip in ip_in_line:
				try:
					line = line.replace(ip, socket.gethostbyaddr(ip)[0]).replace('.baidu.com', '')
				except socket.herror:
					pass
			print line[:-1]
		elif verbose:
			print line[:-1]
	fp.close()
	return 0

def main():
	if len(sys.argv) == 1:
		return ipsum(sys.stdin, verbose = True)
	if len(sys.argv) == 2 and sys.argv[1] == '-o':
		return ipsum(sys.stdin, verbose = False)
	if len(sys.argv) == 2 and sys.argv[1] == '-h':
		return Usage()
	if len(sys.argv) == 2 and sys.argv[1] != '-o':
		try:
			fp = open(sys.argv[1])
		except IOError, errmsg:
			print errmsg
			return -1
		return ipsum(fp, verbose = True)
	if len(sys.argv) == 3 and sys.argv[1] == '-o':
		try:
			fp = open(sys.argv[2])
		except IOError, errmsg:
			print errmsg
			return -1
		return ipsum(fp, verbose = False)
	return Usage()

if __name__ == '__main__':
	sys.exit(main())
