# Everything in a private folder: the vdf fork must not meet Debian's
# python3-vdf in dist-packages.
lib=/usr/lib/protonup-qt
for d in vdf-4.0 steam-2.0.0-alpha1 inputs-0.5 ProtonUp-Qt-2.16.0; do
    python3 -m pip install --no-deps --no-build-isolation --no-index --break-system-packages \
        --target "$DESTDIR$lib" "./$d"
done
rm -rf "$DESTDIR$lib/bin"
install -d "$DESTDIR/usr/bin"
cat >"$DESTDIR/usr/bin/protonup-qt" <<SH
#!/bin/sh
exec python3 -c 'import sys; sys.path.insert(0, "$lib"); from pupgui2.pupgui2 import main; sys.exit(main())' "\$@"
SH
chmod 755 "$DESTDIR/usr/bin/protonup-qt"
# The desktop entry runs net.davidotek.pupgui2.
ln -s protonup-qt "$DESTDIR/usr/bin/net.davidotek.pupgui2"
cp -r ProtonUp-Qt-2.16.0/share "$DESTDIR/usr/"
