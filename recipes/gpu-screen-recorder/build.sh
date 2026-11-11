meson setup build --prefix=/usr --buildtype=release -Dcapabilities=false -Dnvidia_suspend_fix=false
meson compile -C build
meson install -C build --destdir "$DESTDIR"
