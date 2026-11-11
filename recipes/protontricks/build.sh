cd protontricks-1.15.0
# The tag tarball has no git metadata for setuptools-scm; Debian's layout
# puts the module in /usr/lib/python3/dist-packages.
export SETUPTOOLS_SCM_PRETEND_VERSION=1.15.0 DEB_PYTHON_INSTALL_LAYOUT=deb_system
python3 -m pip install --no-deps --no-build-isolation --no-index --break-system-packages \
    --root "$DESTDIR" --prefix /usr .
