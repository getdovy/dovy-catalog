cd libdvdcss-1.6.0
meson setup build --prefix=/usr --libdir=lib/x86_64-linux-gnu --buildtype=release
meson compile -C build
meson install -C build --destdir "$DESTDIR"
rm -r "$DESTDIR/usr/include" "$DESTDIR/usr/lib/x86_64-linux-gnu/pkgconfig" "$DESTDIR/usr/lib/x86_64-linux-gnu/libdvdcss.so" \
	"$DESTDIR/usr/lib/x86_64-linux-gnu/libdvdcss.a" "$DESTDIR/usr/share/doc/libdvdcss"
install -Dm644 COPYING "$DESTDIR/usr/share/doc/libdvdcss2/copyright"
