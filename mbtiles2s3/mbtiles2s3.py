#!/usr/bin/env python

"""
mbtiles2s3 reads in a MBTiles file and exports to S3
"""

import logging, os, sys, json, urllib, argparse, sqlite3, zlib
import progressbar
import boto
from boto.s3.cors import CORSConfiguration


class MBTiles2S3():
  """
  Class to handle conversion.  This is built as a command line tool
  and not meant for library inclusion.
  """

  description = """
examples:

  Export an mbtiles file to an S3 bucket:
  $ mbtiles2s3 world.mbtiles bucket.example

  Export an mbtiles file to an S3 bucket and path:
  $ mbtiles2s3 world.mbtiles bucket.example -p path/to/tiles

  Use a Mapbox box directly to an S3 bucket and path:
  $ mbtiles2s3 -m mapbox_user.map_id bucket.example -p path/to/tiles


requirements:

  It is expected to have AWS credentials set as AWS_ACCESS_KEY_ID and
  AWS_SECRET_ACCESS_KEY.  These can be set on the command line like:

    export AWS_ACCESS_KEY_ID="xxxxx";
    export AWS_SECRET_ACCESS_KEY="xxxx";
  """

  default_acl = 'public-read'
  mime_png = 'image/png'
  mime_json = 'application/json'
  mime_jsonp = 'text/javascript'
  mime_mbtiles = 'application/octet-stream'


  def __init__(self):
    """
    Constructor.
    """
    self.default_cors = CORSConfiguration()
    self.default_cors.add_rule('GET', '*', allowed_header = '*')
    self.main()


  def out(self, message):
    """
    Wrapper around stdout
    """
    sys.stdout.write(message)


  def error(self, message):
    """
    Wrapper around stderror
    """
    sys.stderr.write(message)


  def connect_s3(self):
    """
    Makes connection to S3 and gets the bucket to work in.
    """
    self.out('- Connecting to S3 and making bucket.\n')
    self.s3 = boto.connect_s3()
    self.bucket = self.s3.create_bucket(self.bucket_name)
    self.bucket = self.s3.get_bucket(self.bucket_name)
    self.bucket.set_acl(self.default_acl)
    self.bucket.set_cors(self.default_cors)


  def connect_mbtiles(self):
    """
    Connect to the MBTiles file which is just an sqlite file.
    """
    try:
      self.out('- Connecting to MBTiles.\n')
      self.mbtiles = sqlite3.connect(self.source)
    except Exception as e:
      self.error('Could not connect to MBTiles.\n')
      sys.exit(1)


  def send_file(self, path, content = None, mime_type = None, file = None, cb = None):
    """
    Send a file to S3 given a path and conent.
    """
    mime_type = self.mime_png if mime_type is None else mime_type
    path = self.path + '/' + path if self.path else path

    # TODO: CORS headers don't seem to be set on new resource

    # Create resource at path
    key = self.bucket.new_key(path)
    key.content_type = mime_type

    # Set content
    if file is not None:
      key.set_contents_from_filename(file, replace = True, cb = cb, num_cb = 100)
    else:
      key.set_contents_from_string(content, replace = True)

    # Set access
    self.bucket.set_acl(self.default_acl, key)



  def jsonp(self, content):
    """
    Make data into JSON and wrap if needed.
    """
    metadata = json.dumps(self.metadata, sort_keys = True)
    mime_type = self.mime_json

    if self.args.callback is not None and self.args.callback != '':
      metadata = '%s(%s);' % (self.args.callback, metadata)
      mime_type = self.mime_jsonp

    return (metadata, mime_type)


  def mbtiles_metadata(self):
    """
    Get metadata and upload.
    """
    self.metadata = dict(self.mbtiles.execute('select name, value from metadata;').fetchall())
    (metadata, mime_type) = self.jsonp(self.metadata)
    self.send_file(self.tileset + '.json', metadata, mime_type)
    self.send_file(self.tileset + '/metadata.json', metadata, mime_type)
    self.out('- Uploaded metadata.\n')


  def mbtiles_image_tiles(self):
    """
    Get image tiles and upload.
    """
    tile_count = self.mbtiles.execute('select count(zoom_level) from tiles;').fetchone()[0]

    # Progress bar
    widgets = ['- Uploading %s image tiles: ' % (tile_count), progressbar.Percentage(), ' ', progressbar.Bar(), ' ', progressbar.ETA()]
    progress = progressbar.ProgressBar(widgets = widgets, maxval = tile_count).start()
    completed = 0

    # Get tiles
    tiles = self.mbtiles.execute('select zoom_level, tile_column, tile_row, tile_data from tiles;')
    t = tiles.fetchone()
    while t:
      key = '%s/%s/%s/%s.png' % (self.tileset, t[0], t[1], t[2])
      self.send_file(key, t[3])

      # Get next and update
      t = tiles.fetchone()
      completed = completed + 1
      progress.update(completed)

    # Stop progress bar
    progress.finish()


  def mbtiles_grid_tiles(self):
    """
    Get grid tiles and upload.
    """
    tile_count = self.mbtiles.execute('select count(zoom_level) from grids;').fetchone()[0]

    # Progress bar
    widgets = ['- Uploading %s grid tiles: ' % (tile_count), progressbar.Percentage(), ' ', progressbar.Bar(), ' ', progressbar.ETA()]
    progress = progressbar.ProgressBar(widgets = widgets, maxval = tile_count).start()
    completed = 0

    # Get tiles
    tiles = self.mbtiles.execute('select zoom_level, tile_column, tile_row, grid from grids;')
    t = tiles.fetchone()
    while t:
      key = '%s/%s/%s/%s.grid.json' % (self.tileset, t[0], t[1], t[2])

      # Get actual json data
      grid_data = self.mbtiles.execute('select key_name, key_json FROM grid_data WHERE zoom_level = %s and tile_column = %s and tile_row = %s;' % (t[0], t[1], t[2])).fetchall()
      grid_data_parse = {}
      for d in grid_data:
        grid_data_parse[d[0]] = json.loads(d[1])

      # Put together
      grid = json.loads(zlib.decompress(t[3]).decode('utf-8'))
      grid['data'] = grid_data_parse

      # Upload data
      (grid, mim_type) = self.jsonp(grid)
      self.send_file(key, grid, mime_type = mime_type)

      # Get next and update
      t = tiles.fetchone()
      completed = completed + 1
      progress.update(completed)

    # Stop progress bar
    progress.finish()


  def mbtiles_mbtiles(self):
    """
    Upload original mbtiles.
    """
    key = '%s.mbtiles' % (self.tileset)

    widgets = ['- Uploading MBTile file: ', progressbar.Percentage()]
    progress = progressbar.ProgressBar(widgets = widgets, maxval = 1).start()

    # Progress callback
    def report_progress(complete, total):
      progress.update(float(complete) / float(total))

    self.send_file(key, file = self.source, cb = report_progress, mime_type = mime_mbtiles)
    progress.finish()


  def get_mapbox_mbtiles(self):
    """
    Download file from Mapbox.
    """
    mapbox_mbtiles = 'http://a.tiles.mapbox.com/v3/%s.mbtiles'
    local_mbtiles = '%s.mbtiles'
    remote_file = mapbox_mbtiles % (self.source)
    local_file = local_mbtiles % (self.source)

    # Check if file exists already
    if os.path.exists(local_file) and os.path.isfile(local_file):
      self.out('- Local file, %s, already exists; using this file.\n' % (local_file))
    else:
      self.out('- Downloading file from Mapbox ...\n')
      urllib.urlretrieve (remote_file, local_file)

    self.source = local_file


  def main(self):
    """
    The main execution of the class and handles CLI arguments.
    """
    parser = argparse.ArgumentParser(description = self.description, formatter_class = argparse.RawDescriptionHelpFormatter,)

    # Source
    parser.add_argument(
      'source',
      help = 'The .mbtiles file source.  If used with the --mapbox-source flag, then this should be a Mapbox map identifier.'
    )

    # Bucket
    parser.add_argument(
      'bucket',
      help = 'The S3 bucket to send to.'
    )

    # Bucket path
    parser.add_argument(
      '-p', '--path',
      dest = 'path',
      help = 'Path in bucket to send to.',
      default = ''
    )

    # Option to add jsonp wrapper
    parser.add_argument(
      '-g', '--grid-callback',
      dest = 'callback',
      help = 'Control JSONP callback for UTFGrid tiles.  Defaults to `grid`, use blank to remove JSONP',
      default = 'grid'
    )

    # Tileset name
    parser.add_argument(
      '-t', '--tileset-name',
      dest = 'tileset_name',
      help = 'The name of the tileset to use.  By default, this will be the file name of the source.',
      default = ''
    )

    # Option to use Mapbox file
    parser.add_argument(
      '-m', '--mapbox-source',
      action = 'store_true',
      help = 'Use this flag to interpret the source as a Mapbox map, usually in the format of `user.map_id`.'
    )

    # Do not upload mbtiles
    parser.add_argument(
      '-u', '--dont-upload-mbtiles',
      action = 'store_true',
      help = 'Do not upload the original mbtiles file.  This is desierable for archivable purposes.'
    )

    # Do not upload image tiles
    parser.add_argument(
      '-i', '--dont-upload-image-tiles',
      action = 'store_true',
      help = 'Do not upload the image tiles.'
    )

    # Do not upload grid tiles
    parser.add_argument(
      '-r', '--dont-upload-grid-tiles',
      action = 'store_true',
      help = 'Do not upload the grid tiles.'
    )

    # Turn on debugging
    parser.add_argument(
      '-d', '--debug',
      action = 'store_true',
      help = 'Turn on debugging.'
    )

    # Parse options
    args = parser.parse_args()

    # Set some properties
    self.args = args
    self.source = args.source
    self.bucket_name = args.bucket
    self.path = args.path

    # Debugging
    if self.args.debug:
      logging.basicConfig(level = logging.DEBUG)

    # If mapbox option, handle that
    if self.args.mapbox_source:
      self.get_mapbox_mbtiles()

    # Ensure that the file exists
    if not os.path.exists(self.source) or not os.path.isfile(self.source):
      self.error('The source file is not a file or does not exist.\n')
      sys.exit(1)

    # Ensure that we have AWS credentials set up
    if 'AWS_ACCESS_KEY_ID' not in os.environ or 'AWS_SECRET_ACCESS_KEY' not in os.environ:
      self.error('AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY not found in the environment.\n')
      sys.exit(1)

    # Determine tileset name
    self.tileset = self.args.tileset_name
    if self.tileset is None or self.tileset == '':
      self.tileset = os.path.splitext(os.path.basename(self.source))[0]

    # Normalize the path
    self.path = os.path.normcase(self.path.strip('/'))

    # Make initial connection to S3
    self.connect_s3()

    # Make initial connection to mbtiles
    self.connect_mbtiles()

    # Upload metadata
    self.mbtiles_metadata()

    # Upload tiles
    if not self.args.dont_upload_image_tiles:
      self.mbtiles_image_tiles()
    if not self.args.dont_upload_grid_tiles:
      self.mbtiles_grid_tiles()

    # Upload mbtiles
    if not self.args.dont_upload_mbtiles:
      self.mbtiles_mbtiles()

    # Done
    self.out('- Done.\n')



# Handle execution
if __name__ == '__main__':
  mbtiles2s3 = MBTiles2S3()
