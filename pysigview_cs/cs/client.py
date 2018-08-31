#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 29 09:23:17 2017

Basic client

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

# Third party imports
import zmq
import numpy as np

# Local imports


class PysigviewClient:

    def __init__(self, ip='127.0.0.1', port='5557'):

        self.ip = ip
        self.port = port
        self.socket = None

        self.recording_metadata = None
        self.data_map = None

    def connect(self):

        print("Connecting to server...")
        context = zmq.Context()
        self.socket = context.socket(zmq.REQ)
        self.socket.connect("tcp://{}:{}".format(self.ip, self.port))

    def set_file_handler(self, path, password=''):

        print('Setting file handler')
        request = {'set_fh': [path, password]}

        self.socket.send_pyobj(request)
        res = self.socket.recv_pyobj()

        return res

    def request_directory_tree(self):

        request = {'directory_tree': []}
        print("Sending request ", request, "...")
        self.socket.send_pyobj(request)
        dir_tree = self.socket.recv_pyobj()

        return dir_tree

    def request_metadata(self):

        request = {'metadata': []}
        self.socket.send_pyobj(request)
        rmd, dm = self.socket.recv_pyobj()

        self.recording_metadata = rmd
        self.data_map = dm

        return rmd, dm

    def request_annotations(self):

        request = {'annotations': []}
        self.socket.send_pyobj(request)
        annots = self.socket.recv_pyobj()

        return annots

    def request_data_simple(self, channel_map, uutc_map):

        self.data_map.reset_data_map()

        if isinstance(channel_map, str):
            self.data_map.set_channel(channel_map, uutc_map)
        elif (isinstance(channel_map, list)
              and not isinstance(uutc_map[0], list)):
            for ch in channel_map:
                self.data_map.set_channel(ch, uutc_map)
        else:
            for ch, uutc in zip(channel_map, uutc_map):
                self.data_map.set_channel(ch, uutc)

        self.socket.send_pyobj({'data': [self.data_map]})
        data = self.socket.recv_pyobj()

        return np.vstack([x for x in data if len(x)])

    def request_data_data_map(self, dm):

        self.socket.send_pyobj({'data': [dm]})
        data = self.socket.recv_pyobj()

        return data

    def closes(self):
        self.socket.close()

    def terminate_server(self):
        self.socket.send_pyobj({'terminate': []})
