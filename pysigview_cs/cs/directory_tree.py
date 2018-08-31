#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 29 09:23:17 2017

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
from collections import OrderedDict

# Third party imports

# Local imports


class DiretoryTree:

    def __init__(self, path):

        self.d = self.path_to_dict(path)
        self.extensions = []

    def __repr__(self):

        return self.print_path_dictionary(self.d)

    def __str__(self):

        return self.print_path_dictionary(self.d)

    @property
    def extensions(self):
        return self._ext

    @extensions.setter
    def extensions(self, ext):
        self._ext = ext

    def path_to_dict(self, path):
        d = {'name': os.path.basename(path)}
        if os.path.isdir(path):
            d['type'] = "directory"
            d['children'] = [self.path_to_dict(os.path.join(path, x))
                             for x in os.listdir(path)]
        else:
            d['type'] = "file"
        return OrderedDict(sorted(d.items(), key=lambda t: t[0]))

    def clean_tree(self):
        self.clean_path_dictionary(self.d)

    def clean_path_dictionary(self, d):

        if 'children' in d.keys():
            new_children = []
            for child in d['children']:

                # Check files for extension
                if child['type'] == 'file':
                    if any([True for x in self._ext
                            if child['name'].endswith(x)]):
                        new_children.append(child)
                else:
                    # Check directory for extension - and cut it if OK
                    if any([True for x in self._ext
                            if child['name'].endswith(x)]):
                        if 'children' in child.keys():
                            del child['children']
                            new_children.append(child)
                    else:
                        self.clean_path_dictionary(child)

                        # Check we did not leave empty directory
                        if 'children' in child.keys():
                            new_children.append(child)

            if len(new_children):
                d['children'] = sorted(new_children, key=lambda k: k['name'])
            else:
                del d['children']

    def print_path_dictionary(self, subd, level=0):

        out_str = '\t'*level+subd['name']+'('+subd['type']+')\n'
        if 'children' in subd.keys():
            for child in subd['children']:
                out_str = out_str + self.print_path_dictionary(child, level+1)

        return out_str
