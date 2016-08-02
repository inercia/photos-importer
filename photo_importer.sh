#/!bin/sh

ARGS="-r --sort %Y/%Y-%m-%d --rename %Y%m%d%H%M%S"

log()         { echo ">>> $@" ; }
error()       { log "ERROR: $@" ; }
abort()       { log "FATAL: $@" ; exit 1 ; }
abs()         { cd "$1" && pwd ; }

##################################################

[ $# -ge 2 ] || abort "wrong numer of arguments"

while [[ $# > 2 ]] ; do
    ARGS="$1 $ARGS"
    shift
done
ORIG=$1
shift
DEST=$1
shift

##################################################

echo "Synchronizing: '$ORIG' -> '$DEST'"
[ -d $ORIG ] || abort "$ORIG is not a valid directory"
[ -d $DEST ] || abort "$DEST is not a valid directory"

docker run --rm -ti \
    -v $(abs $ORIG):/orig -v $(abs $DEST):/dest \
    inercia/photos-importer \
    photos_importer $ARGS /orig /dest
