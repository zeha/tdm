from __future__ import print_function
import datetime
import urlparse
import sys
import argparse
import sqlite3

parser = argparse.ArgumentParser()
parser.add_argument('-F', dest='fields', default='_tracker,ratio,uploaded,downloaded,latest_activity,name')
parser.add_argument('-f', dest='where', default='1')
args = parser.parse_args()

args.fields = args.fields.split(',')


torrents = []
torrent = None

db = sqlite3.connect(':memory:')
dbc = db.cursor()

lines = sys.stdin.readlines()
for line in lines:
	line = line.rstrip()
	if line == 'NAME':
		if torrent is not None:
			torrents.append(torrent)
		torrent = {}
	elif ': ' in line:
		k, v = line.split(': ', 1)
		k = k.strip().replace(' ', '_').lower()
		v = v.strip()
		if v == 'None':
			v = 0
		elif v == 'Inf':
			v = 9999
		if k in ['date_added', 'date_finished', 'date_started', 'latest_activity']:
			v = datetime.datetime.strptime(v, "%a %b %d %H:%M:%S %Y")
		elif k in ['ratio']:
			v = float(v)
		elif k in ['magnet']:
			url = urlparse.parse_qs(urlparse.urlparse(urlparse.urlparse(v).query.replace('btih:','btih/').replace('&','?',1)).query)['tr'][0]
			torrent['_tracker'] = urlparse.urlparse(url).netloc.split(':')[0].split('.')[-2]
		else:
			v = str(v).decode('UTF-8')
		torrent[k] = v

def coldefs(names):
	return ','.join(['"%s" TEXT' % (name,) for name in names])

def flatten(l):
	return [item for sublist in l for item in sublist]

def quote_join_list(names):
	return ','.join([('"%s"' % n) for n in names])

fields = set(flatten([t.keys() for t in torrents]))
create_table = "CREATE TABLE torrents (%s)" % coldefs(fields)
dbc.execute(create_table)

for t in torrents:
	keys = t.keys()
	insert = "INSERT INTO torrents (%s) VALUES (%s)" % (quote_join_list(keys), ','.join(['?' for k in keys]))
	dbc.execute(insert, [t[k] for k in keys])

query = 'SELECT %s FROM torrents WHERE %s' % (quote_join_list(args.fields), args.where)
for row in dbc.execute(query):
	print(*[x for x in row])

