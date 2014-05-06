#!/usr/bin/env python

#
# mbtiles2s3 reads in a MBTiles file and exports to S3
#

import logging, os, sys
import urllib
import argparse
import boto


# Class for tool
class MBTiles2S3():
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


  # Std out
  def out(self, message):
    sys.stdout.write(message)


  # Std error
  def error(self, message):
    sys.stderror.write(message)


  # Connect to S3
  def connect_s3(self):
    self.out('Creating connection to S3 and making bucket.\n')
    self.s3 = boto.connect_s3()
    self.bucket = self.s3.create_bucket(self.bucket_name)
    self.bucket.set_acl(self.default_acl)


  # Get file from Mapbox
  def get_mapbox_mbtiles(self):
    mapbox_mbtiles = 'http://a.tiles.mapbox.com/v3/%s.mbtiles'
    local_mbtiles = '%s.mbtiles'
    remote_file = mapbox_mbtiles % (self.source)
    local_file = local_mbtiles % (self.source)

    # Check if file exists already
    if os.path.exists(local_file) and os.path.isfile(local_file):
      self.out('Local file, %s, already exists, using this file.\n' % (local_file))
    else:
      self.out('Downloading file from Mapbox ...\n')
      urllib.urlretrieve (remote_file, local_file)

    self.source = local_file


  # Main execution
  def main(self):
    # Main program
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
      help = 'Option to control JSONP callback for UTFGrid tiles.  Defaults to `grid`, use blank to remove JSONP',
      default = 'grid'
    )

    # Option to use Mapbox file
    parser.add_argument(
      '-m', '--mapbox-source',
      action = 'store_true',
      help = 'Use this flag to interpret the source as a Mapbox map, usually in the format of `user.map_id`.'
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

    # Make initial connection to S3
    self.connect_s3()



# Handle execution
if __name__ == '__main__':
  mbtiles2s3 = MBTiles2S3()
  mbtiles2s3.main();
