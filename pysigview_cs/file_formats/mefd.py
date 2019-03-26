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

# Third pary imports
import numpy as np
import pandas as pd

from pymef.mef_session import MefSession

# Local imports
from ..source_manager import FileDataSource


class mefdHandler(FileDataSource):
    def __init__(self):
        super(mefdHandler, self).__init__()

        self.name = 'Mef session'
        self.extension = '.mefd'

        self.session = None

    def password_check(self, password):

        try:
            if self.session is None:
                self.session = MefSession(self._path, password, False,
                                          check_all_passwords=False)
            return True
        except RuntimeError as e:
            return False

    def load_metadata(self):

        if self.session is None or self.session.session_md is None:
            self.session = MefSession(self._path, self._password,
                                      check_all_passwords=False)

        # Get information about the recording

        s_md = self.session.session_md['session_specific_metadata']
        ts_md = self.session.session_md['time_series_metadata']['section_2']
        ts_ch = self.session.session_md['time_series_channels']
        channel_list = list(ts_ch.keys())
        channel_list.sort()
        self.recording_info = {}
        self.recording_info['recording_start'] = s_md['earliest_start_time'][0]
        self.recording_info['recording_end'] = s_md['latest_end_time'][0]
        self.recording_info['recording_duration'] = (
                ts_md['recording_duration'][0])
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
            channel_md = ts_ch[channel]
            fsamp = channel_md['section_2']['sampling_frequency'][0]
            nsamp = channel_md['section_2']['number_of_samples'][0]
            ufact = channel_md['section_2']['units_conversion_factor'][0]
            unit = channel_md['section_2']['units_description'][0]
            unit = unit.decode("utf-8")

            channel_spec_md = channel_md['channel_specific_metadata']
            start_time = channel_spec_md['earliest_start_time'][0]
            end_time = channel_spec_md['latest_end_time'][0]

            toc = self.session.get_channel_toc(channel)
            disc_stops = toc[3, toc[0] == 1]
            disc_starts = disc_stops - toc[1, toc[0] == 1]
            disconts = np.c_[disc_starts, disc_stops]

            dmap[i] = (fsamp, nsamp, ufact, unit, channel, disconts,
                       True, [start_time, end_time])

        self.data_map.setup_data_map(dmap)

    def _process_mef_records(self, records_list):
        """
        Processes records generated by pymef and puts them into Pysigview.
        """

        # Basic annotation columns
        basic_cols = ['start_time', 'end_time', 'channel']

        dfs_out = {}

        for entry in records_list:
            rec_header = entry['record_header']
            rec_body = entry['record_body']
            rec_type = rec_header['type_string'][0]
            rec_type = rec_type.decode("utf-8")
            if rec_type not in dfs_out:
                ann_cols = [x[0] for x in rec_body.dtype.descr]
                cols = basic_cols + ann_cols
                dfs_out[rec_type] = pd.DataFrame(columns=cols)

            df = dfs_out[rec_type]
            ei = len(df)
            col_vals = {'start_time': rec_header['time'][0],
                        'end_time': np.nan,
                        'channel': np.nan}
            col_vals.update(
                    dict([(x[0], rec_body[x[0]][0])
                          for x in rec_body.dtype.descr]))
            # Convert byte strings to normal strings
            for key, val in col_vals.items():
                if type(val) == np.bytes_:
                    col_vals[key] = (val.decode("utf-8"))

            df.loc[ei] = col_vals

        return dfs_out

    def get_annotations(self):
        """
        Returns:
        --------
        Annotations - in form of pandas DataFrame(s)
        """

        if self.session is None or self.session.session_md is None:
            self.session = MefSession(self._path, self._password)

        dfs_out = {}
        session_md = self.session.session_md
        # Get session level records
        if 'records_info' in session_md.keys():
            session_records = session_md['records_info']['records']

            dfs_out.update(self._process_mef_records(session_records))

        # Get channel level records
        for _, channel_d in session_md['time_series_channels'].items():
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

        data = self.session.read_ts_channels_uutc(channel_map, uutc_map)

        data_out = np.empty(len(data_map), object)
        for i in range(len(data_map)):
            data_out[i] = np.array([], dtype='float32')
        for i, ch in enumerate(channel_map):
            ch_pos = np.argwhere(data_map['channels'] == ch)[0][0]
            data_out[ch_pos] = data[i]

        return data_out
