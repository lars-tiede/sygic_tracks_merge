#!/usr/bin/python

# Copyright 2013 Lars Tiede (lars.tiede@gmail.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import struct
import datetime
from collections import OrderedDict
import argparse
#import xml.etree.ElementTree as ET

import gpxpy
import gpxpy.gpx



class SygicLogReader(object) :
    """Understands travelbook log files version 5 (those beginning with '5FRT')

    Usage :
    >>> log = SygicLogReader(filename)
    >>> print log.header
    >>> for point in log.read_points() :
            print point["lat"]
            print point["lon"]
            print point["time"]

    header is a dict, and the available fields (names taken from unofficial documentation of file format
    version 4) are:
    "favorite" (int) - don't know what this means
    "log type" (byte) - don't know what this means
    "log start time" (long) - don't know what this means (doesn't look like a timestamp??)
    "log duration" (long) - don't know what this means (number doesn't check out with actual length of log)
    "log length" (long) - don't know what this means (value is usually the same as "log duration")
    "start log point description" - name of the place on the map where log started (usually a road address)
    "end log point description" - name of the place on the map where log stopped (usually a road address)
    "start time string" - string of the format YYMMDD_HHMMSS_OOO (hour in 24h format, OOO an offset in minutes (WTF!?)), local time zone
    "programmed destination description" - name of the place on the map which was programmed as nav destination
    "end lon" (long) - I think this is the longitude of the place where the log stopped. Move decimal point 5 places to the left.
    "end lat" (long) - I think this is the latitude of the place where the log stopped. Move decimal point 5 places to the left.
    "point count" (long) - Number of points in log

    Each point is returned as a dictionary from read_points(), and the available fields (names taken from
    unofficial documentation of file format version 4) are:
    "lon" (long) - longitude. Move decimal point 5 places to the left.
    "lat" (long) - latitude. Move decimal point 5 places to the left.
    "alt" (long) - altitude, in meters. Not corrected for systematic error (where I live, values are consistently around 32m too high)
    "time" (long) - time elapsed since first point in log was recorded, in ms. (Value is 0 for first point)
    "speed" (float) - speed, probably in km/h.
    "signal quality" (byte) - don't know what this means (value usually 3 in the logs I looked at)
    "speeding" (byte) - don't know what this means (value usually 0 or small >0 in my logs)
    "gsm signal quality" (byte) - don't know what this means (value usually 3 in my logs)
    "internet signal quality" (byte) - don't know what this means (value usually 2 in my logs)
    "battery status" (byte) - don't know what this means (value usually -1 in my logs)
    """

    # struct format specs - headers
    _fmt_header_v5_strlen = '<H'
    _fmt_header_version = '<cccc'
    _fmt_header_v5 = '<ibLLL'
    _fmt_header_v5_elem = ["favorite", "log type", "log start time",
                          "log duration", "log length"] # "last mark distance" apparently not there any more
    _fmt_points_header = "<llL"
    _fmt_points_header_elem = ["end lon", "end lat", "point count"]

    # struct format specs - data
    _fmt_point = "<llllfbbbbb"
    _fmt_point_elem = ["lon", "lat", "alt", "time", "speed", "signal quality", "speeding", "gsm signal quality", "internet signal quality", "battery status"]


    def __init__(self, fn) :
        self._fn = fn
        self._fp = open(fn, "rb")

        self.header = OrderedDict()
        self._read_header()


    ### Small helper functions

    def _struct_unpack_from_file(self, fmt) :
        return struct.unpack(fmt, self._fp.read(struct.calcsize(fmt)))

    def _read_wide_string(self) :
        strlen = self._struct_unpack_from_file(self._fmt_header_v5_strlen)[0]
        data = self._fp.read(strlen*2)
        return data.decode('utf-16')


    ### Reading and understanding the Sygic log file

    def _read_header(self) :
        self.header = OrderedDict()

        # read format version magic
        version = self._struct_unpack_from_file(self._fmt_header_version)
        if version != ('5', 'F', 'R', 'T') :
            raise ValueError, "Can't read this file format (version) :("
        self.header["version"] = 5

        # read some fixed length int and byte and word fields
        stuff = self._struct_unpack_from_file(self._fmt_header_v5)
        for key, val in zip(self._fmt_header_v5_elem, stuff) :
            self.header[key] = val

        # read some variable length strings
        self.header["start log point description"] = self._read_wide_string()
        self.header["end log point descriprion"] = self._read_wide_string()
        self.header["start time string"] = self._read_wide_string()
        self.header["programmed destination description"] = self._read_wide_string()

        # read some more fixed length fields (about the points to come)
        stuff = self._struct_unpack_from_file(self._fmt_points_header)
        for key, val in zip(self._fmt_points_header_elem, stuff) :
            self.header[key] = val


    def read_points(self) :
        """Generator yielding each point as a dictionary. See class doc for details on available fields."""
        for i in xrange(self.header["point count"]) :
            yield dict(zip(self._fmt_point_elem, self._struct_unpack_from_file(self._fmt_point)))



class GpxWriter(object) :
    """Makes a GPX file with one track out of several segments. API is stateful: init this, then make a
    new segment, add points to that, then make a new segment, etc."""

    def __init__(self, fp, track_name, track_description) :
        self._fp = fp
        self._gpx = gpxpy.gpx.GPX()
        self._track = gpxpy.gpx.GPXTrack(name = track_name, description = track_description)
        self._gpx.tracks.append(self._track)

        self._segment_cur = None

    def new_segment(self) :
        self._segment_cur = gpxpy.gpx.GPXTrackSegment()
        self._track.segments.append(self._segment_cur)

    def add_point(self, lat, lon, elev, time, speed) :
        """lat and lon are floats, elev an int (m), time TODO NO IDEA, and speed TODO NO IDEA"""
        point = gpxpy.gpx.GPXTrackPoint(lat, lon, elevation=elev, time=time, speed=speed)
        self._segment_cur.points.append(point)

    def write_gpx_file(self) :
        self._fp.write( self._gpx.to_xml() )
        self._fp.flush()



def convert_sygic_log_to_gpx_tracksegment(sygic_log, gpx_writer, time_zone_correction=0) :
    """time_zone_correction relative to UTC (hours). Example: EST -> -5. CET -> +1. CEST -> +2.
    This function does not make a new track segment by itself, it uses only gpx_writer.add_point"""
    # determine start time from sygic log: parse first part of time string
    time_start = datetime.datetime.strptime(sygic_log.header["start time string"][:13], "%y%m%d_%H%M%S")
    # now add the stupid offset at the end of that string
    time_start += datetime.timedelta(minutes=int(sygic_log.header["start time string"][-3:]))
    # finally, fiddle in time zone correction (local = UTC + offset --> UTC = local - offset)
    time_start -= datetime.timedelta(hours=time_zone_correction)

    for point in sygic_log.read_points() :
        # convert point data from sygic log to gpx conventions, then add point to gpx writer
        lat = float(point["lat"]) * 0.00001
        lon = float(point["lon"]) * 0.00001
        elev = point["alt"]
        speed = point["speed"] * 0.277777777777778 # from km/h to m/s

        ts = time_start + datetime.timedelta(milliseconds=point["time"])
        #ts_text = ts.strftime("%Y-%m-%dT%H:%M:%SZ")

        gpx_writer.add_point(lat, lon, elev, ts, speed)



def main(fns_in, fn_out, tz_offset, track_name, track_desc) :
    fp_out = None
    if not fn_out :
        fp_out = sys.stdout
    else :
        fp_out = file(fn_out, "wb")

    gpx_writer = GpxWriter(fp_out, track_name, track_desc)

    for fn_in in fns_in :
        log = SygicLogReader(fn_in)
        gpx_writer.new_segment()
        convert_sygic_log_to_gpx_tracksegment(log, gpx_writer, tz_offset)

    gpx_writer.write_gpx_file()
    fp_out.close()



if __name__ == "__main__" :
    parser = argparse.ArgumentParser(description='convert and merge several sygic travelbook logs to a gpx file')
    parser.add_argument("-o", "--outFile", default="", metavar="gpx_output_file",
            help="path to GPX output file")
    parser.add_argument("-n", "--trackName", default="", metavar="track_name",
            help="name of the (merged) track in the generated GPX file")
    parser.add_argument("-d", "--trackDesc", default="", metavar="track_description",
            help="description of the (merged) track in the generated GPX file")
    parser.add_argument("-t", "--tzOffset", type=int, default=0, metavar="offset",
            help="time zone offset in sygic log files relative to UTC (in hours). Examples: EST -5, CET 1, CEST 2")
    parser.add_argument("inFiles", metavar="sygic_log_file",
            nargs='+', help="path to sygic travelbook log file(s) to convert and merge")
    args = parser.parse_args()

    main(args.inFiles, args.outFile, args.tzOffset, args.trackName, args.trackDesc)
