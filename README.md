# mbtiles2s3

A simple command line tool to export MBTiles to an S3 location.

## Install

    git clone https://github.com/MinnPost/mbtiles2s3.git;
    cd mbtiles2s3;
    python setup.py install;

## Usage

    mbtiles2s3 source bucket [options]

## Requirements

In order to upload to S3, you will need to set your AWS credentials.

    export AWS_ACCESS_KEY_ID="xxxxx";
    export AWS_SECRET_ACCESS_KEY="xxxx";

### Examples

Export an mbtiles files to a bucket.

    mbtiles2s3 ./world.mbtiles bucket.example

Export an mbtiles files to a sub directory within a bucket.

    mbtiles2s3 ./world.mbtiles bucket.example -p tiles-subdirectory

A convenient method for getting a Mapbox mbtiles can be use, just use your map ID as the source

    mbtiles2s3 user-account.map-id bucket.example -m

### Final structure

Given the name of your mbtiles file is `world-example.mbtiles`, you will end up with the following in your bucket within the path if it is specified:

    world-example.json
    world-example.mbtiles
    world-example/
      metadata.json
      11/
        11/
          11.png
          11.grid.json
