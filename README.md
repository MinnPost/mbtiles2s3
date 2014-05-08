# mbtiles2s3

A simple command line tool to export MBTiles to an S3 location.

## Install

    git clone https://github.com/MinnPost/mbtiles2s3.git;
    cd mbtiles2s3;
    python setup.py install;

## Requirements

In order to upload to S3, you will need to set your AWS credentials.

    export AWS_ACCESS_KEY_ID="xxxxx";
    export AWS_SECRET_ACCESS_KEY="xxxx";

## Usage

Output from `mbtiles2s3 --help`:


    usage: mbtiles2s3.py [-h] [-p PATH] [-g CALLBACK] [-t TILESET_NAME] [-m] [-r]
                         [--dont-upload-mbtiles] [--dont-upload-image-tiles]
                         [--dont-upload-grid-tiles] [-d]
                         source bucket

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


    positional arguments:
      source                The .mbtiles file source. If used with the --mapbox-
                            source flag, then this should be a Mapbox map
                            identifier.
      bucket                The S3 bucket to send to.

    optional arguments:
      -h, --help            show this help message and exit
      -p PATH, --path PATH  Path in bucket to send to.
      -g CALLBACK, --grid-callback CALLBACK
                            Control JSONP callback for UTFGrid tiles. Defaults to
                            `grid`, use blank to remove JSONP
      -t TILESET_NAME, --tileset-name TILESET_NAME
                            The name of the tileset to use. By default, this will
                            be the file name of the source.
      -m, --mapbox-source   Interpret the source as a Mapbox map, usually in the
                            format of `user.map_id`.
      -r, --remove-first    Remove old files first. This is good if for some
                            reason the map boundary has changed.
      --dont-upload-mbtiles
                            Do not upload the original mbtiles file. This is
                            desierable for archivable purposes.
      --dont-upload-image-tiles
                            Do not upload the image tiles.
      --dont-upload-grid-tiles
                            Do not upload the grid tiles.
      -d, --debug           Turn on debugging.


## Final structure

Given the name of your mbtiles file is `world-example.mbtiles`, you will end up with the following in your bucket within the path if it is specified:

    world-example.json
    world-example.mbtiles
    world-example/
      metadata.json
      11/
        11/
          11.png
          11.grid.json
