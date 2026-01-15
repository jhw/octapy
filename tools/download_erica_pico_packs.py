#!/usr/bin/env python

"""
Download Erica Synths Pico Drum sample packs from their official server.
Saves samples to tmp/Erica Pico/{pack-name}/{sample-name}.wav
"""

import json
import os
import re
import urllib.request

Endpoint = "http://data.ericasynths.lv/picodrum"

def fetch_json(path, endpoint = Endpoint):
    return json.loads(urllib.request.urlopen(f"{endpoint}/{path}").read())

def pack_list():
    return {item["name"]:item["file"] for item in fetch_json("pack_list.json")}

def fetch_bin(path, endpoint = Endpoint):
    return urllib.request.urlopen(f"{endpoint}/{path}").read()

def directory_name(pack_name):
    pack_slug = pack_name.lower().replace(" ", "-")
    return f"tmp/Erica Pico/{pack_slug}"

def filter_blocks(buf):
    def format_block(i, block):
        tokens = block.split(b"data")
        name = tokens[0][1:-1]
        data = (b"data".join(tokens[1:]))
        offset = data.index(b"RIFF")
        return (i, name, data[offset:])
    return [format_block(i, block.split(b"<?xpacket begin")[0])
            for i, block in enumerate(buf.split(b"\202\244name")[1:])]

def init_project(fn):
    def wrapped(pack_name, pack_file):
        dir_name = directory_name(pack_name)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        return fn(pack_name, pack_file)
    return wrapped

@init_project
def dump_blocks(pack_name, pack_file):
    dir_name = directory_name(pack_name)
    buf = fetch_bin(pack_file)
    blocks = filter_blocks(buf)
    for i, block_name, block in blocks:
        tokens = block_name.decode('utf-8').split(".")
        stub, ext  = re.sub("\\W", "", "".join(tokens[:-1])), tokens[-1]
        file_name = f"{dir_name}/{stub}.{ext}"
        with open(file_name, 'wb') as f:
            f.write(block)

if __name__ == "__main__":
    try:
        for pack_name, pack_file in pack_list().items():
            print(pack_name)
            dump_blocks(pack_name, pack_file)
    except RuntimeError as error:
        print ("Error: %s" % str(error))
