Sygic travel book log file merger and GPX exporter
==================================================

As of 2013-03-09, the [Sygic](http://www.sygic.com/en) satellite navigation system allows users to track travels in a so-called travel book, but if you want to use the travel book logs in another application, you're stuck with a poor KML export that doesn't even contain for example timestamps for each logged point. If you want to use the travel book logs to geotag photos you took on a road trip for example (which is what I wanted to do), you're out of luck.

This command line utility allows you to read one or several Sygic travel book log files in Sygic's proprietary and undocumented binary format, and convert them into one GPX file that retains most of the interesting information from the binary log files - all information that I understand, that is. The resulting GPX file can be read by various applications. For example, [Adobe Lightroom](http://www.adobe.com/products/photoshop-lightroom.html) can read GPX files to automatically geotag pictures you took while Sygic was logging your position.

Usage
-----

    $ sygic_tracks_merge.py -o output.gpx SYGIC_LOG_FILE(S)

will read all specified sygic log files, and produce one gpx file (output.gpx). The output file contains one track, with one track segment for each input log file.

This is how you can make one GPX file out of a whole day's worth of Sygic travel book log files:

    $ sygic_tracks_merge.py -o 20130309.gpx path/to/log/files/20130309*.log

If you happen to have been in another time zone than UTC, you want to specify the time zone offset relative to UTC, because Sygic logs in local time only. For example EST:

    $ sygic_tracks_merge.py -o 20130309.gpx -t -5 path/to/log/files/20130309*.log

To get documentation on all available command line options, just call

    $ sygic_tracks_merge.py --help

There are options to apply time zone correction, and to set a name and description for the track in the GPX file.

Details on Sygic's binary log file format
-----------------------------------------

[This blog post](http://fleckenzwerg2000.blogspot.no/2013/03/merging-sygic-travel-book-log-files-and.html) goes into detail about what I have found out about Sygic's proprietary, binary, and closed travel book log file format.

License
-------

sygic_tracks_merge is licensed under the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).

External libraries
------------------

[gpxpy](https://github.com/tkrajina/gpxpy) by Tomo Krajina is used to make GPX files. gpxpy is licensed under the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).

Further acknowledgements
------------------------

Thanks to Paul, the author of [Sygiclog](http://p-l-j.dyndns.org/PLJ/sygiclog/). That tool was the only place where I found (outdated) information about Sygic's log file format.
