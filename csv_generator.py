#!/usr/bin/env python

from argparse import ArgumentParser

import os
import logging
import pynmea2
import pandas as pd
import re

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)


def raw_to_csv(infile, outfile):
    ext = os.path.splitext(infile)[1]
    if (ext != '.txt') and (ext != '.log'):
        logging.warning('Skip! {} is not a regular input file'.format(infile))
        return

    if os.path.exists(outfile):
        logging.info('Skip! Output file {} exists.'.format(outfile))
        return

    logging.info('Generating {}...'.format(outfile))

    ds = None
    df = pd.DataFrame()

    f = open(infile, encoding='utf-8')
    for line in f.readlines():
        string = re.search('(\$).*', line)
        try:
            msg = pynmea2.parse(string.group())
        except AttributeError:
            continue
        except pynmea2.ParseError as e:
            # logging.warning('Parse error: {}'.format(e))
            continue

        if isinstance(msg, pynmea2.types.talker.GGA):
            if ds is not None:
                df = df.append(ds, ignore_index=True)
                ds = None
            ds = pd.Series(index=['datestamp' ,'timestamp', 'longitude', 'latitude', 'gps_qual', 'num_sats', 'spd_over_grnd', 'true_course', 'heading'], dtype='object')
            ds.timestamp = msg.timestamp
            ds.longitude = msg.longitude
            ds.latitude = msg.latitude
            ds.gps_qual = msg.gps_qual
            ds.num_sats = msg.num_sats
        elif isinstance(msg, pynmea2.types.talker.RMC):
            if ds is not None:
                ds.datestamp = msg.datestamp
                ds.spd_over_grnd = msg.spd_over_grnd
                ds.true_course = msg.true_course
        elif isinstance(msg, pynmea2.types.talker.HDT):
            if ds is not None:
                ds.heading = msg.heading

    if ds is not None:
        df = df.append(ds, ignore_index=True)

    df = df.loc[:, ['datestamp','timestamp', 'longitude', 'latitude', 'gps_qual', 'num_sats','spd_over_grnd', 'true_course', 'heading']]
    df.to_csv(outfile, index=False)


def main(args):
    path = os.path.abspath(args.path)
    if os.path.isfile(path):
        infile = path
        _, fn = os.path.split(infile)
        outfile = os.path.splitext(infile)[0] + '.csv'
        raw_to_csv(infile, outfile)
    elif os.path.isdir(path):
        root = path
        indir = os.path.join(root, 'raw')
        outdir = os.path.join(root, 'csv')
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        logging.info('Scan folder: {}'.format(indir))
        infiles = [os.path.join(indir, f) for f in os.listdir(indir) if os.path.isfile(os.path.join(indir, f))]
        for infile in infiles:
            _, fn = os.path.split(infile)
            outfile = os.path.join(outdir, os.path.splitext(fn)[0] + '.csv')
            raw_to_csv(infile, outfile)
    else:
        logging.warning('Invalid path: {}'.format(path))


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('path', help='path')

    args = parser.parse_args()

    main(args)