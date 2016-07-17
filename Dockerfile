FROM python:onbuild

RUN wget http://http.us.debian.org/debian/pool/main/libi/libimage-exiftool-perl/libimage-exiftool-perl_9.74-1_all.deb && dpkg -i libimage-exiftool-perl_9.74-1_all.deb

VOLUME ["/photos/src", "/photos/dst"]
WORKDIR /photos/src

CMD ["sortphotos"]
