#!/usr/bin/env python

from argparse import ArgumentParser

import os
import logging
import shutil
import pandas as pd
import simplekml

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)


icons = [os.path.join('icon', f) for f in os.listdir('icon') if os.path.isfile(os.path.join('icon', f))]
icon_url = dict()
icon_url['arrow'] = '../icon/arrow.png'
icon_url['forbidden'] = '../icon/forbidden.png'


def csv_to_kml(infile, outfile):

    ext = os.path.splitext(infile)[1]
    if (ext != '.csv'):
        logging.warning('Skip! {} is not a regular input file'.format(infile))
        return

    if os.path.exists(outfile):
        logging.info('Skip! Output file {} exists.'.format(outfile))
        return

    logging.info('Generating {} ...'.format(outfile))

    f = open(infile, encoding='utf-8')
    df = pd.read_csv(f)

    kml = simplekml.Kml()
    trk = kml.newgxtrack(name='Track', altitudemode=simplekml.AltitudeMode.clamptoground)
    pnts = kml.newdocument(name='Points')
    lines = kml.newdocument(name='Lines')

    playlist = kml.newgxtour(name="Tour").newgxplaylist()
    # tracker = kml.newdocument(name='Tracker')
    for _, row in df.iterrows():
        if row.gps_qual > 0:
            break

    tracker = kml.newpoint(name='', coords = [(row.longitude, row.latitude)])
    tracker.style.iconstyle.icon.href = icon_url['arrow']
    tracker.style.iconstyle.scale = 0.7
    tracker.style.iconstyle.heading = 0
    tracker.style.iconstyle.hotspot = simplekml.HotSpot(x=0.5,y=0.5, xunits='fraction', yunits='fraction')

    # full view
    flyto = playlist.newgxflyto(gxduration=1.0,gxflytomode='smooth')
    flyto.camera.longitude = row.longitude
    flyto.camera.latitude = row.latitude
    flyto.camera.altitude = 5000
    wait = playlist.newgxwait(gxduration=3.0)

    flyto = playlist.newgxflyto(gxduration=5.0,gxflytomode='smooth')
    flyto.camera.longitude = row.longitude
    flyto.camera.latitude = row.latitude
    flyto.camera.altitude = 250

    prev = None
    for _, row in df.iterrows():
        if row.gps_qual < 1:
            continue
        # track
        add_to_track(row, trk)

        # point
        add_to_points(row, pnts)

        # linestring
        if prev is None:
            ls = lines.newlinestring()
        elif prev.gps_qual != row.gps_qual:
            ls = lines.newlinestring()
        ls.altitudemode = simplekml.AltitudeMode.clamptoground

        add_to_linestring(row, ls)

        # tour
        add_to_playlist(row, playlist, tracker)

        prev = row

    trk.iconstyle.icon.href = icon_url['arrow']
    trk.iconstyle.hotspot = simplekml.HotSpot(x=0.5,y=0.5, xunits='fraction', yunits='fraction')

    kml.save(outfile)


def add_to_track(data, trk):
    trk.newwhen('{}T{}'.format(data.datestamp, data.timestamp))
    trk.newgxcoord([(data.longitude, data.latitude)])


def add_to_points(data, points):
    pnt = points.newpoint(name='', coords = [(data.longitude, data.latitude)])
    if data.gps_qual == 1:   # GPS Fix
        pnt.style.iconstyle.icon.href = icon_url['arrow']
        pnt.style.iconstyle.scale = 0.3
        pnt.style.iconstyle.color = simplekml.Color.orange
    elif data.gps_qual == 2: # DGPS Fix
        pnt.style.iconstyle.icon.href = icon_url['arrow']
        pnt.style.iconstyle.scale = 0.3
        pnt.style.iconstyle.color = simplekml.Color.yellow
    elif data.gps_qual == 4: # RTK Fix
        pnt.style.iconstyle.icon.href = icon_url['arrow']
        pnt.style.iconstyle.scale = 0.3
        pnt.style.iconstyle.color = simplekml.Color.green
    else:
        pnt.style.iconstyle.icon.href = icon_url['forbidden']
        pnt.style.iconstyle.color = 'FF0000FF'
        pnt.style.iconstyle.hotspot = simplekml.HotSpot(x=0.5,y=0.5, xunits='fraction', yunits='fraction')

    if data.true_course is not None:
        pnt.style.iconstyle.heading = data.true_course

    pnt.style.iconstyle.hotspot = simplekml.HotSpot(x=0.5,y=0.5, xunits='fraction', yunits='fraction')


def add_to_linestring(data, ls):
    ls.coords.addcoordinates([(data.longitude, data.latitude)])

    ls.style.linestyle.width = 5

    if data.gps_qual == 1:
        ls.name = 'GPS fixed'
        ls.style.linestyle.color = simplekml.Color.orange
    elif data.gps_qual == 2:
        ls.name = 'DGPS fixed'
        ls.style.linestyle.color = simplekml.Color.yellow
    elif data.gps_qual == 4:
        ls.name = 'RTK fixed'
        ls.style.linestyle.color = simplekml.Color.green
    else:
        ls.name = 'GPS quality indicator = {}'.format(data.gps_qual)
        ls.style.linestyle.color = simplekml.Color.red
        logging.warning('Unprocessed GPS quality indicator: {}'.format(data.gps_qual))

def add_to_playlist(data, playlist, tracker):

    animatedupdate = dict()
    animatedupdate['position'] = playlist.newgxanimatedupdate(gxduration=0.05)
    animatedupdate['position'].update.change = '<Point targetId="{}"><coordinates>{},{},0.0</coordinates></Point>'.format(tracker.id, data.longitude, data.latitude)

    if data.true_course:
        animatedupdate['orientation'] = playlist.newgxanimatedupdate(gxduration=0.05)
        animatedupdate['orientation'].update.change = '<IconStyle targetId="{}"><heading>{}</heading></IconStyle>'.format(tracker.style.iconstyle.id, data.true_course)

    flyto = playlist.newgxflyto(gxduration=0.05,gxflytomode='smooth')
    flyto.camera.longitude = data.longitude
    flyto.camera.latitude = data.latitude
    flyto.camera.altitude = 250
    flyto.camera.tilt = 0
    flyto.camera.heading = 0
    flyto.camera.roll = 0
    flyto.camera.altitudemode = simplekml.AltitudeMode.relativetoground


def main(args):
    path = os.path.abspath(args.path)
    if os.path.isfile(path):
        infile = path
        _, fn = os.path.split(infile)
        outfile = os.path.splitext(infile)[0] + '.kml'
        csv_to_kml(infile, outfile)
    elif os.path.isdir(path):
        root = path
        indir = os.path.join(root, 'csv')
        outdir = os.path.join(root, 'kml')
        icondir = os.path.join(root, 'icon')
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        if not os.path.exists(icondir):
            os.makedirs(icondir)

        for f in icons:
            shutil.copy(f, os.path.join(root, 'icon', ''))

        logging.info('Scan folder: {}'.format(indir))
        infiles = [os.path.join(indir, f) for f in os.listdir(indir) if os.path.isfile(os.path.join(indir, f))]
        for infile in infiles:
            _, fn = os.path.split(infile)
            outfile = os.path.join(outdir, os.path.splitext(fn)[0] + '.kml')
            csv_to_kml(infile, outfile)
    else:
        logging.warning('Invalid path: {}'.format(path))


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('path', help='path')
    parser.add_argument('--icon', help='icon_url', default='arrow.png')

    args = parser.parse_args()

    main(args)