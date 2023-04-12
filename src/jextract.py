#!/usr/bin/env python
"""trivial field extractor for json

jextract.py is intended to be used to cut fields from json data.
Text table format is the default output format, but can be changed to 
TSV with the -t option, or to another delimiter with with the -d option.

jextract.py will also auto-detect array input when the first line starts with '['
use -s/--smart to disable this smartness

jextract.py also provide (basic) flattening for extracting nested fields.
nested json can be flattened with --flatten, and if so, nested keys
wan be references with the syntax key1 + . + key2 + index
e.g. name.first or addresses.0.zipcode
Use --join to join keys with a different delimiter, like "|"

jq is a much better alternative for many things, but for my
common use case of slicing out some fields, it's overly verbose.

EXAMPLES:
    # field extraction. Reads from stdin by default.
    $ echo '{"a": 1, "b": 2, "c":3}' | jextract.py c a
    c  a
    3  1


    # extract  from a file, not stdin. Default is to read from stdin.
    $ echo '{"a": 1, "b": 2, "c":3}' > /tmp/jxtmp
    $ jextract.py c a -i /tmp/jxtmp
    c  a
    3  1

    # columnar output is the default. No fields prints all values
    $ printf '{"a": "foo", "b": 1}\n{"a":"loooooong", "b":2}' | jextract.py
    foo        1
    loooooong  2

    # no headers
    $ echo '{"a": 1, "b": 2, "c":3}' | jextract.py -H c a
    3  1

    # flatten
    $ echo '{"a": {"b": 2, "c":3, "d":[5,6] }}' | jextract.py -F a_c a_b
    a_c  a_b
    3    2

    # flatten with dot
    # with -f or -F, should be easy to separate keys from parents
    $ echo '{"a": {"b": 2, "c":3, "d":[5,6] }}' | jextract.py -f a.c a.b
    a.c  a.b
    3    2

    # flatten with array indexing, taking the first element of an array
    $ echo '{"a": {"b": 2, "c":3, "d": [7,10]}}' | jextract.py -F a_c a_d_0
    a_c	 a_d_0
    3    7

    # get field names from first line
    echo '{"a": 1, "b": 2, "c":3}' | jextract.py --names
    a
    b
    c

    # alternate json level joiner. Default is '.'
    $  echo '{"a": {"b": 2, "c":3, "d":[5,6] }}' | jextract.py -F -j. a.c a.b
    a.c  a.b
    3    2  
    
    # tab-separated output
    $ echo '{"a":1, "b": 2, "c":3}' | jextract.py  -t a c
    a	c
    1	3

    # alternate output delimiter
    $ echo '{"a":1, "b": 2, "c":3}' | jextract.py  -s '|'  a c
    a|c
    1|3

    # collapse whitespace in output fields, useful for columnar output
    $ echo '{"first": "Jud D"}' | jextract.py -w
    first
    Jud_D

    # smart parsing: autodetect arrays
    echo '[{"a":1},{"a":2}]' | jextract.py a
    a
    1
    2

    # smart detecting multiline arrays (json pretty printed)
    echo '[{"a":1},{"a":2}]' | jq | jextract.py a
    a
    1
    2

    # extract all keys from all objects
    printf '{"b":1,"a":2}\n{"b":2,"c":3}' | jextract.py --all-keys
    b
    a
    c

    
TODO:
    Add positional field extraction. Will require validation of fields on every
    line to match the first line to prevent silently dropping/munging columns

"""

from __future__ import print_function
import argparse
import json
import logging
import sys


class Flattener:
    def __init__(self, joiner="_"):
        self.joiner = joiner

    def flatten(self, data, out=None, prefix=None):
        out = {} if out is None else out
        prefix = [] if prefix is None else prefix

        if isinstance(data, dict):
            for k, value in data.items():
                self.flatten(value, out, prefix + [k])
        elif isinstance(data, list):
            for counter, value in enumerate(data):
                self.flatten(value, out, prefix + [counter])
        else:
            key = self.joiner.join([str(s) for s in prefix])
            logging.debug(f"writing {data} to {key}")
            out[key] = data
        return out


class ColumnPrinter:
    def __init__(self, joiner="  "):
        self.joiner = joiner
        self.rows = []

    def print(self, columns):
        self.rows.append(columns)

    def flush(self):
        # logging.debug("rows: %s", self.rows)

        # compute the width for each column, by taking the max of each field's
        # width. Note that this takes the number of columns from the first row.
        # https://stackoverflow.com/a/12065663

        widths = [max(map(len, col)) for col in zip(*self.rows)]
        logging.debug("column widths: %s", widths)
        for row in self.rows:
            padded = [val.ljust(width) for val, width in zip(row, widths)]
            if padded:
                padded[-1] = list(row)[-1]  # don't pad the last field
                line = self.joiner.join(padded)
                print(line)


class DelimitedPrinter:
    def __init__(self, joiner):
        self.joiner = joiner

    def print(self, columns):
        print(self.joiner.join(columns))

    def flush(self):
        pass


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description="%(prog)s extract fields easily from json")

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-t', '--tsv', action='store_const', const="\t",
                       dest="delimiter", help='tab-delimited output. Also see --delimiter')
    group.add_argument('-d', '--delimiter', help='delimiter for json fields/columns')

    group2 = parser.add_mutually_exclusive_group()
    group2.add_argument('-n', '--names', action='store_true',
                        help='show column names from initial object and exit')
    group2.add_argument('-N', '--all-names', action='store_true',
                        help="print unique key names from all objects in the order they appear")

    group3 = parser.add_mutually_exclusive_group()
    group3.add_argument('-F', '--flatten', action='store_true',
                        help='flatten json before selecting. uses the --joiner')
    group3.add_argument('-f', '--flatten-dot', action='store_true',
                        help='flatten json before selecting. uses "." as joiner')

    parser.add_argument('-j', '--joiner',
                        help='joiner for keynames when flattening levels, ' +
                             'e.g. "key1_key2". Default: %(default)s', default='_')
    parser.add_argument('-H', '--headers', action='store_true',
                        help="skip header printing")
    parser.add_argument('-s', '--smart', action='store_false',
                        default='True',
                        help='disable smart detection of arrays')
    parser.add_argument('-D', '--debug', action='store_true',
                        help='debug')
    parser.add_argument('-w', '--whitespace', action='store_true',
                        help="translate whitespace to _ in fields")
    parser.add_argument('--infile', '-i', type=argparse.FileType(),
                        help='alternate input file. Default is stdin',
                        default=sys.stdin)
    parser.add_argument('fields', nargs="*",
                        help="list of field names to extract.")

    options = parser.parse_args(args=args)
    if options.flatten_dot:
        options.flatten = True
        options.joiner = '.'

    return options


def parse_first(first_line, fh, opts) -> list[dict]:
    logging.debug('smartly checking first line: %s', first_line)
    stripped = first_line.strip()
    if stripped.startswith('['):
        logging.info("array detected")
        first_line = first_line + fh.read()
        return json.loads(first_line)

    if stripped == '{':
        logging.info("multiline json object detected.")
        first_line = first_line + fh.read()

    parsed = json.loads(first_line)

    # standard object on the first line for JSONL data
    return [parsed]


def read(fh, opts) -> dict:
    first_line = ""
    while first_line.strip() == "":
        first_line = fh.readline()

    for parsed_row in parse_first(first_line, fh, opts):
        yield parsed_row

    for line in fh:  # one object per line
        logging.debug(f">>>{line.strip()}<" + "\n")
        if not line.strip():
            logging.debug('skipping')
            continue
        yield json.loads(line)


def print_all_keys(objects, flattener=None) -> None:
    seen_keys = set()
    for ob in objects:
        if flattener:
            ob = flattener.flatten(ob)
        for key in ob.keys():
            if key not in seen_keys:
                print(key)
                seen_keys.add(key)


def run(opts):
    if opts.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    if opts.delimiter is not None:
        printer = DelimitedPrinter(opts.delimiter)
    else:
        printer = ColumnPrinter()

    flattener = Flattener(joiner=opts.joiner)

    if opts.fields and not opts.headers:
        printer.print(opts.fields)

    if opts.all_names:
        flatten = flattener if opts.flatten else None
        print_all_keys(read(opts.infile, opts), flattener=flatten)
        return

    for data in read(opts.infile, opts):
        if opts.flatten:
            data = flattener.flatten(data)
        if opts.names:
            for k in data.keys():
                print(k)
            return

        logging.debug(data.keys())

        if not opts.headers and not opts.fields:
            logging.warning("taking field names from first object. use -H to disable")
            opts.fields = data.keys()
            printer.print(opts.fields)

        # if we have a list of fields, use them. Otherwise, print all keys
        fields = [str(data.get(f, "")) for f in opts.fields or data.keys()]

        if opts.whitespace:
            fields = [f.replace(" ", "_") for f in fields]

        logging.debug(fields)
        printer.print(fields)

    printer.flush()


def cli(args=None):
    logging.basicConfig(level=logging.INFO)
    opts = parse_args(args=args)
    run(opts)


if __name__ == '__main__':
    cli()
