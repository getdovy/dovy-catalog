cd ProtonPlus-0.6.8
meson setup build --prefix=/usr --buildtype=release
meson compile -C build
meson install -C build --destdir "$DESTDIR"
