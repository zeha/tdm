from __future__ import print_function
import datetime
import urlparse
import sys
import argparse
import sqlite3

SIZE_NAMES = ['B', 'kB', 'MB', 'GB', 'TB', 'PB']
DB_TYPES = {'ratio': 'NUMERIC', 'downloaded': 'INTEGER', 'uploaded': 'INTEGER'}

parser = argparse.ArgumentParser()
parser.add_argument('-F', dest='fields', default='_tracker,ratio,uploaded,downloaded,latest_activity,name')
parser.add_argument('-f', dest='where', default='1')
args = parser.parse_args()

args.fields = args.fields.split(',')


torrents = []
torrent = None

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
		elif k in ['downloaded', 'uploaded']:
			if isinstance(v, str):
				v = v.split(' ', 1)
				v = int(float(v[0]) * (1024**SIZE_NAMES.index(v[1])))
		elif k in ['ratio']:
			v = float(v)
		elif k in ['magnet']:
			url = urlparse.parse_qs(urlparse.urlparse(urlparse.urlparse(v).query.replace('btih:','btih/').replace('&','?',1)).query)['tr'][0]
			torrent['_tracker'] = urlparse.urlparse(url).netloc.split(':')[0].split('.')[-2]
		else:
			v = str(v).decode('UTF-8')
		torrent[k] = v

def coldefs(names):
	return ','.join(['"%s" %s' % (name, DB_TYPES.get(name, 'TEXT')) for name in names])

def flatten(l):
	return [item for sublist in l for item in sublist]

def quote_join_list(names):
	return ','.join([('"%s"' % n) for n in names])

def format_size(val):
	for name in SIZE_NAMES:
		if val < 1024:
			break
		val /= 1024
	return "%.2f %s" % (val/1.024, name)

def format_row(row):
	data = []
	for k in row.keys():
		v = row[k]
		if k in ['uploaded', 'downloaded']:
			v = format_size(float(v))
		data.append(v)
	return data

db = sqlite3.connect(':memory:')
db.row_factory = sqlite3.Row
dbc = db.cursor()

fields = set(flatten([t.keys() for t in torrents]))
create_table = "CREATE TABLE torrents (%s)" % coldefs(fields)
dbc.execute(create_table)

for t in torrents:
	keys = t.keys()
	insert = "INSERT INTO torrents (%s) VALUES (%s)" % (quote_join_list(keys), ','.join(['?' for k in keys]))
	dbc.execute(insert, [t[k] for k in keys])

query = 'SELECT %s FROM torrents WHERE %s' % (quote_join_list(args.fields), args.where)
for row in dbc.execute(query):
	print(*[x for x in format_row(row)])

