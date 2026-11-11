cd ghostty-1.4.0
export ZIG_GLOBAL_CACHE_DIR=/build/zig-cache
../zig-x86_64-linux-0.17.1/zig build --prefix /usr -Doptimize=ReleaseFast -Dcpu=baseline -Dversion-string=1.4.0
# Zig keeps the sources' group-write bit.
chmod -R go-w "$DESTDIR"
