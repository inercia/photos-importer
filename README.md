# photos-importer

An automatic photos importer that:

1. watches (recursively) a directory for new photos
2. copies/moves the photos to a new directory
3. renames these photos according to some rules

It is based on the [sortphotos](https://github.com/andrewning/sortphotos)
python utility, but enhanced for being used as a daemon. Check the
_sortphotos_ arguments for an overview of how to use it.

## Usage

The `photos-importer` is intended to be used as a container. You should
run the Docker container with:

```
docker run --rm -ti \
    -v $(abs $ORIG):/orig -v $(abs $DEST):/dest \
    inercia/photos-importer \
    photos_importer \
    -r --sort %Y/%Y-%m-%d --rename %Y%m%d%H%M%S \
    /orig /dest
```

where `$ORIG` and `$DEST` are the origin and destination for
your photos.
