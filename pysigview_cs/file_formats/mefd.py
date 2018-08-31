#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 26 09:02:11 2017

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

# Std imports
import os

# Third pary imports
import numpy as np
import pandas as pd

from pymef import read_ts_channels_uutc, get_toc
from pymef import pymef3_file

# Local imports
from ..source_manager import FileDataSource


class mefdHandler(FileDataSource):
    def __init__(self):
        super(mefdHandler, self).__init__()

        self.name = 'Mef session'
        self.extension = '.mefd'

    def check_password(self, password):

        # Get one .tdat file and test it (shuold the C function do this?)
        for root, subfolds, files in os.walk(self._path):
            if len([x for x in files if '.tdat' in x]):
                tdat_file = [x for x in files if '.tdat' in x][0]
                break

        if pymef3_file.check_mef_password(root+'/'+tdat_file, password) < 0:
            return False
        else:
            return True

    def load_metadata(self):

        session_md = pymef3_file.read_mef_session_metadata(self._path,
                                                           self._password,
                                                           False)

        # Get information about the recording
        spec_md = session_md['session_specific_metadata']
        ts_md = session_md['time_series_metadata']['section_2']
        channel_list = list(session_md['time_series_channels'].keys())
        channel_list.sort()

        self.recording_info = {}
        self.recording_info['recording_start'] = spec_md['earliest_start_time']
        self.recording_info['recording_end'] = spec_md['latest_end_time']
        self.recording_info['recording_duration'] = ts_md['recording_duration']
        self.recording_info['extension'] = '.mefd'
        self.recording_info['nchan'] = len(channel_list)

        dmap = np.zeros(len(channel_list),
                        dtype=[('fsamp', np.float, 1),
                               ('nsamp', np.int32, 1),
                               ('ufact', np.float, 1),
                               ('unit', np.object, 1),
                               ('channels', np.object, 1),
                               ('discontinuities', np.ndarray, 1),
                               ('ch_set', np.bool, 1),
                               ('uutc_ss', np.int64, 2)])

        for i, channel in enumerate(channel_list):
            channel_md = session_md['time_series_channels'][channel]
            fsamp = channel_md['section_2']['sampling_frequency']
            nsamp = channel_md['section_2']['number_of_samples']
            ufact = channel_md['section_2']['units_conversion_factor']
            unit = channel_md['section_2']['units_description']

            channel_spec_md = channel_md['channel_specific_metadata']
            start_time = channel_spec_md['earliest_start_time']
            end_time = channel_spec_md['latest_end_time']

            toc = get_toc(channel_md)
            disc_stops = toc[3, toc[0] == 1]
            disc_starts = disc_stops - toc[1, toc[0] == 1]
            disconts = np.c_[disc_starts, disc_stops]

            dmap[i] = (fsamp, nsamp, ufact, unit, channel, disconts,
                       True, [start_time, end_time])

        self.data_map.setup_data_map(dmap)

    def _process_mef_records(self, records_list):
        """
        Processes records generated by pymef and puts them into sigpy format.
        """

        # Basic annotation columns
        basic_cols = ['start_time', 'end_time', 'channel']

        # Ignored params
        ignored_params = ['type_string', 'version_minor', 'version_major',
                          'bytes', 'encryption', 'record_CRC']

        dfs_out = {}

        for entry in records_list:
            if entry['type_string'] not in dfs_out:
                ann_cols = list(entry['record_body'].keys()
                                - ignored_params)
                cols = basic_cols + ann_cols
                dfs_out[entry['type_string']] = pd.DataFrame(columns=cols)

            df = dfs_out[entry['type_string']]
            ei = len(df)
            col_vals = {'start_time': entry['time'],
                        'end_time': np.nan,
                        'channel': np.nan}
            col_vals.update(dict([i for i in entry['record_body'].items()
                                  if i[0] not in ignored_params]))
            df.loc[ei] = col_vals

        return dfs_out

    def get_annotations(self):
        """
        Returns:
        --------
        Annotations - in form of pandas DataFrame(s)
        """

        session_md = pymef3_file.read_mef_session_metadata(self._path,
                                                           self._password,
                                                           False)

        dfs_out = {}

        # Get session level records
        if 'records_info' in session_md.keys():
            session_records = session_md['records_info']['records']

            dfs_out.update(self._process_mef_records(session_records))

        # Get channel level records
        for channel, channel_d in session_md['time_series_channels'].items():
            if 'records_info' in channel_d.keys():
                ch_rec_list = channel_d['records_info']['records']
            else:
                ch_rec_list = []

            # Get segment level records
            for segment_d in channel_d['segments'].values():
                if 'records_info' in segment_d.keys():
                    ch_rec_list += segment_d['records_info']['records']

            dfs_out.update(self._process_mef_records(ch_rec_list))

        return dfs_out

    def get_data(self, data_map):
        """
        Parameters:
        -----------
        data_map - DataMap instance for loading

        Returns:
        --------
        The data in a list specified by channel_map
        """

        channel_map = data_map.get_active_channels()
        uutc_map = data_map.get_active_uutc_ss()

        data = read_ts_channels_uutc(self._path, self._password,
                                     channel_map, uutc_map)

        data_out = np.empty(len(data_map), object)
        for i in range(len(data_map)):
            data_out[i] = np.array([], dtype='float32')
        for i, ch in enumerate(channel_map):
            ch_pos = np.argwhere(data_map['channels'] == ch)[0][0]
            data_out[ch_pos] = data[i]

        return data_out
