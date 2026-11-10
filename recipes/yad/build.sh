cd yad-14.2
autoreconf -ivf
./configure --prefix=/usr --disable-schemas-compile
make
make install
