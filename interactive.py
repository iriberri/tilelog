# -*- coding: utf-8 -*-
import re
import datetime
import itertools
import random
from collections import namedtuple

LINE_REGEXP = re.compile("""
    <\d+>
    (\d+-\d+-\d+T\d+:\d+:\d+Z) # log timestamp
    \ (?:.*?)\[\d+\]:
    \ (\d+.\d+.\d+.\d+)     # IP address
    \ (?:.*?)\ GET   
    \ /([\w-]+)/api/v1/map/ # user + endpoint
    (?:([\w-]+@\w+)@)?      # named map template (optional)
    (\w+):(\d+(?:\.\d+)?)/  # layergroup ID + timestamp
    /?
    (\d+)/                  # zoom
    (-?\d+)/                # x
    (-?\d+)                 # y
    (?:/-?\d+)?             # torque extra parameter (?)
    \.([\w\.]+)             # extension type
""", re.VERBOSE)

Event = namedtuple("Event", [
    'x', 'y', 'z',
    'time', 'user',
    'ip_address',
    'named_map_template',
    'layergroup',
    'layergroup_timestamp',
    'type'
])

def tilelog(path):
    '''
    tilelog(string path)

    Reads the log provided by parameters and returns a list of Events. Some special lines 
    in the log are ignored.
    '''
    dataset = []
    with open(path) as f:
        for line in f:
            if "/static/bbox/" in line or \
                "/static/center" in line or \
                "/favicon.ico" in line or \
                "MISS 404" in line:
                continue

            m = LINE_REGEXP.match(line)
            if not m:
                raise RuntimeError("Failed to match: " + line)

            dataset.append(Event(
                time=datetime.datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%SZ"),
                ip_address=m.group(2),
                user=m.group(3),
                named_map_template=m.group(4),
                layergroup=m.group(5),
                layergroup_timestamp=\
                    datetime.datetime.utcfromtimestamp(
                        float(m.group(6)) / 1000.0),
                z=int(m.group(7)),
                x=int(m.group(8)),
                y=int(m.group(9)),
                type=m.group(10)
            ))

    return dataset

def tiles(ds):
    '''
    tiles(Event[] ds)

    Given a dataset (list of Events), returns a list of the events that correspond to a
    tile request -- which have .png as extension.
    '''
    return [d for d in ds if d.type == "png"]

def _groupby(ds, keyfunc):
    return itertools.groupby(sorted(ds, key=keyfunc), keyfunc)

def get_random_layergroup(ds):
    '''
    get_random_layergroup(Event[] ds)

    Given a dataset, returns one of the layergroups that the log contains.
    '''
    unique_lg = set(t.layergroup for t in ds)
    return random.choice(list(unique_lg))

def get_random_ip_addr(ds):
    '''
    get_random_ip_addr(Event[] ds)

    Given a dataset, returns one of the IP addresses that requested a resource.
    '''
    unique_ip = set(t.ip_address for t in ds)
    return random.choice(list(unique_ip))

def zoom_stats(ds):
    '''
    zoom_stats(Event[] ds)

    Given a dataset (list of Events), returns the percentage of tiles that were requested
    per each level of zoom. The addition of the percentages for all zooms tends to one.

    Example: # sum(p for _, p in zoom_stats(l)) == 1.0
    '''
    return [(z, float(len(list(f)))/len(ds)) for z, f
            in _groupby(ds, lambda e: e.z)]

def edited_layergroups(ds):
    '''
    edited_layergroup(Event[] ds)

    Given a dataset (list of Events), returns a list of the layergroups that were edited at
    least once and the corresponding timestamps of the editions.
    '''
    timestamps = [(l, set(t.layergroup_timestamp for t in i)) for l, i
            in _groupby(ds, lambda e:e.layergroup)]
    return [(l, [str(t) for t in ts]) for l, ts in timestamps if len(ts) > 1]

def most_requested_events(ds, layergroup):
    '''
    most_requested_events(Event[] ds, string layergroup)

    Given a dataset (list of Events) and a layergroup ID, returns the Z X Y values for the most 
    requested events of the specified layergroup ordered by frequency.
    '''
    ds = [(d.x, d.y, d.z) for d in ds if d.layergroup == layergroup]
    freq = sorted(((ds.count(d), d) for d in set(ds)), key=lambda x: x[0])
    max_freq = max(f for f, _ in freq)
    return [d for f, d in freq if f == max_freq]

def events_by_ip_addr(ds, ip_address):
    '''
    events_by_ip_addr(Event[] ds, string ip_address)

    Given a dataset (list of Events) and an IP address, returns the list of Events that were
    requested from the specified source.
    '''
    return [d for d in ds if d.ip_address == ip_address]

def get_user_activity(ds, ip_address):
    '''
    get_user_activity(Event[] ds, string ip_address)

    Given a dataset (list of Events) and an IP address, returns the request activity of the
    source IP ordered by request timestamp.
    '''  
    events = events_by_ip_addr(ds, ip_address)
    prev_x = None
    prev_y = None
    prev_z = None
    prev_time = None

    for s in events:
        print "Time: %s X: %d, Y: %d    Z: %d" % (s.time, s.x, s.y, s.z)

        if prev_x is not None:
            if s.z > prev_z:
                print "   Zoom in"
            elif s.z < prev_z:
                print "   Zoom out"

            if s.x > prev_x:
                print "   Pan right"
            elif s.x < prev_x:
                print "   Pan left"

            if s.y > prev_y:
                print "   Pan up"
            elif s.y < prev_y:
                print "   Pan down"

        prev_x = s.x
        prev_y = s.y
        prev_z = s.z

def draw_ascii_map(tiles, zoom):
    '''
    draw_ascii_map(Event[] tiles, int zoom) 

    Deprecated: please, use draw_multimap instead.

    Given a set of requested tiles, draws their corresponding position inside an ASCII map.
    The character '#' specifies that a tile was request for those XY coordinates, otherwise, 
    non-requested coordinates are drawn as ' . '. 
    '''
    w = 2 ** zoom
    m = [['.'] * w for _ in range(w)]

    for x, y in tiles:
        m[y][x] = '#'

    return "\n".join(' '.join(l) for l in m)

import PIL.Image
import PIL.ImageDraw
import tempfile

def draw_multimap(tiles, highlight=[]):
    '''
    draw_multimap(Event[] tiles, tiles_dataset[] highlight)

    Given a set of tiles, and assuming a basemap ("basemap.png") colorizes the requested tiles
    according to each level of zoom. The highlight parameter allows to emphasize the more 
    requested tiles, which are drawn as outlined tiles.
    '''
    basemap = PIL.Image.open("basemap.png").convert("RGBA")
    heatmap = PIL.Image.new('RGBA', basemap.size, (255,255,255,0))
    draw = PIL.ImageDraw.Draw(heatmap)
    w, h = basemap.size
    opacity = 22

    for (zoom, t) in _groupby(tiles, lambda x: x[2]):
        zoomw = (2 ** zoom)
        draw_w = w / zoomw
        draw_h = h / zoomw

        if draw_w == 0 or draw_h == 0:
            break

        for x, y, _ in set(t):
            x = x * draw_w
            y = y * draw_h
            draw.rectangle(
                [x, y, x + draw_w, y + draw_h],
                fill=(255,0,0,opacity)
            )

        for x, y, z in highlight:
            if z == zoom: 
                x = x * draw_w
                y = y * draw_h
                draw.rectangle(
                    [x, y, x + draw_w, y + draw_h],
                    outline=(255,0,0,255)
                )

        opacity += 22

    out = PIL.Image.alpha_composite(basemap, heatmap)
    tmp = tempfile.NamedTemporaryFile(
        suffix='.png', prefix='tmpmap_', dir='.', delete=False)

    with tmp.file as f:
        out.save(f, format="png")

    return tmp.name

def draw_layergroup(events, lg):
    '''
    draw_layergroup(Event[] ds, string layergroup)

    Given a dataset (list of Events) and a layergroup ID, retrieves the tiles that correspond
    to the layergroup ID and draws them in a map. The function also computes the most requested
    events for the layergroup which are outlined in the final image.
    '''
    tiles = [(e.x, e.y, e.z) for e in events if e.layergroup == lg]
    highlight = most_requested_events(events, lg)
    return draw_multimap(tiles, highlight)

import urllib2
from io import BytesIO

def build_basemap(zoom, retina=True):
    '''
    build_basemap(int zoom, boolean retina)

    Given a level of zoom, builds a basemap of a valid resolution obtaining the
    needed tiles from an external basemap tile server. If the retina option is set
    as true, tiles are requested with double size.
    '''
    zoomw = (2 ** zoom)
    tile_w = 512 if retina else 256
    w, h = (zoomw * tile_w, zoomw * tile_w)
    basemap = PIL.Image.new('RGBA', (w, h), (255,255,255,255))

    for x in range(zoomw):
        for y in range(zoomw):
            url = "http://3.basemaps.cartocdn.com/light_nolabels/%d/%d/%d%s.png" % (
                zoom, x, y, "@2x" if retina else "")
            print "Requesting %s..." % url
            raw = urllib2.urlopen(url).read()
            tile = PIL.Image.open(BytesIO(raw)).convert("RGBA")
            tile_w, tile_h = tile.size

            basemap.paste(tile, (tile_w * x, tile_h * y))
            del tile

    print "Writing basemap_%d.png (%dx%d)..." % (zoom, w, h)
    basemap.save("basemap_%d.png" % zoom)

