#!/usr/bin/env python3
import argparse
from pysigview_cs.cs.server import PysigviewServer

parser = argparse.ArgumentParser(
        description='Start pysigview server in current directory')
parser.add_argument('--ip',type=str, nargs=1, help='IP address of the server')
parser.add_argument('--port',type=str, nargs=1, help='Port of the server')

args = parser.parse_args()
args_dict = vars(args)

if args_dict['ip'] is not None:
    ip=args_dict['ip'][0]
else:
    ip='*'

if args_dict['port'] is not None:
    port=args_dict['port'][0]
else:
    port='5557'

server = PysigviewServer(ip,port)
server.start()
