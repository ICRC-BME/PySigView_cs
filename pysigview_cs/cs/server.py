#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 29 09:23:17 2017

Basic server

Ing.,Mgr. (MSc.) Jan Cimbálník
Biomedical engineering
International Clinical Research Center
St. Anne's University Hospital in Brno
Czech Republic
&
Mayo systems electrophysiology lab
Mayo Clinic
200 1st St SW
Rochester, MN
United States
"""

# Standard library imports
import os

# Third party imports
import zmq
import bcolz

# Local imports
from pysigview_cs.cs.directory_tree import DiretoryTree
from pysigview_cs.file_formats.formats import (get_available_file_formats,
                                               extension_evaluator)


class PysigviewServer:

    def __init__(self, ip='*', port='5557'):

        self.ip = ip
        self.port = port
        self.socket = None

        self.dir_tree = None
        self.file_handler = None

        self.build_directory_tree()

    def build_directory_tree(self):
        print("Creating directory tree")
        self.dir_tree = DiretoryTree(os.getcwd())
        self.dir_tree.extensions = [x.extension
                                    for x in get_available_file_formats()]
        self.dir_tree.clean_tree()

    def set_file_handler(self, path, password):

        abs_path = '/'.join(os.getcwd().split('/')[:-1] + [path])
        print(abs_path)
        fh, ext = extension_evaluator(abs_path)
        if not fh.password_check(password):
            self.socket.send_pyobj(False)
            return
        else:
            fh.password = password

        self.file_handler = fh
        self.socket.send_pyobj(True)

    def send_metadata(self):

        if self.file_handler is None:
            self.socket.send_pyobj(None)
            return

        self.file_handler.load_metadata()
        md = (self.file_handler.recording_info, self.file_handler.data_map)
        self.socket.send_pyobj(md)

    def send_annotations(self):

        annot = self.file_handler.get_annotations()

        self.socket.send_pyobj(annot)

    def send_data(self, dm):

        if self.file_handler is None:
            self.socket.send_pyobj(None)
            return

        data = self.file_handler.get_data(dm)

        self.socket.send_pyobj(data)

    def send_directory_tree(self):
        self.socket.send_pyobj(self.dir_tree)

    def start(self):

        print("Starting the server")
        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        self.socket.bind("tcp://{}:{}".format(self.ip, self.port))
        while True:

            req = self.socket.recv_pyobj()
            print("Received request: ", req)

            req_key = list(req.keys())[0]

            if req_key == 'directory_tree':
                self.send_directory_tree(*req[req_key])

            elif req_key == 'set_fh':
                self.set_file_handler(*req[req_key])

            elif req_key == 'metadata':
                self.send_metadata(*req[req_key])

            elif req_key == 'annotations':
                self.send_annotations(*req[req_key])

            elif req_key == 'data':
                self.send_data(*req[req_key])

            elif req_key == 'terminate':
                self.socket.close()
                break
