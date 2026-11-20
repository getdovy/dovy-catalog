# Recipe format

A recipe is `recipes/<name>/recipe.toml`, plus `build.sh` for kinds that
build. Unknown fields are an error.

## Catalog layout

| Path | Holds |
|---|---|
| `recipes/<name>/` | `recipe.toml`, and `build.sh` for kinds that build |
| `repositories/<name>.toml` | vendor apt repositories, shared by recipes |
| `catalog.toml` | `dovy = "X.Y.Z"`: the oldest dovy that can read this release; set by maintainers |

## Common fields

| Field | Type | Required | Meaning |
|---|---|---|---|
| `name` | string | yes | equals the folder name; `[a-z0-9][a-z0-9.+-]*` |
| `description` | string | yes | one line, no final period |
| `kind` | string | yes | `upstream-build`, `upstream-binary`, `vendor-repository`, `testing-rebuild`, `setup`, `bundle`, `local-build` |
| `version` | string | yes | exact upstream version; never "latest" |
| `revision` | int | no | default 1; bumped when the recipe changes and `version` does not |
| `maintainer` | string | yes | who keeps it updated |
| `debian` | list of ints | yes | Debian releases supported, e.g. `[13]` |
| `requires` | list | no | capabilities: `i386`, `components`, `backports` |
| `depends` | list | no | other recipes, e.g. `nvflux` → `["nvidia"]`; installed with it, and a new one comes with `upgrade` |
| `conflicts` | list | no | the other half of a pair |
| `replaces` | list | no | Debian packages it replaces; required when it does. Same name: newer version. Other name: `Conflicts`. Restored on removal |
| `hardware` | string | no | a named check built into dovy: `nvidia-turing` (every NVIDIA GPU in NVIDIA's open-module table) |
| `secure-boot` | string | no | `dkms` or `unsigned-kernel`: what it needs under Secure Boot; dovy explains, runs nothing |
| `network` | string | no | why a build needs the network |
| `successor` | string | no | the recipe that takes over from this one |
| `user-notes` | string | no | per-user steps, one copy-and-paste command each |

## Per kind

| Kind | Fields |
|---|---|
| `upstream-build` | `[[source]]` (`url`, `sha256`; archives: `.tar.gz`, `.tar.xz`, `.zip`; several are unpacked side by side, e.g. a toolchain); `build.sh`, run in the sandbox in the unpacked sources with `DESTDIR` set; `build-depends` (Debian packages, sandbox only); `packages`: what it needs at run time beyond what is installed, so the plan is complete before the build. `Depends` come from `dpkg-shlibdeps`; a library neither listed, pulled by the list, nor installed stops the run before install; `[scripts]` for what the build's own install step would do as root, e.g. `setcap` |
| `upstream-binary` | `[[source]]` (`url`, `sha256`): a vendor .deb, repacked with dovy's version and `X-Dovy-Recipe`; several .deb sources (distinct packages, e.g. a kernel's image and headers) are each repacked, and the recipe's own package depends on them at their exact versions; `[scripts]` (`preinst`, `postinst`, `prerm`, `postrm`) replaces the vendor's, `""` drops one; `config` and `templates` can only be dropped, with the package's debconf questions; `[[file]]` only `/etc/default/<name>`, read by the vendor's own scripts, shipped as a conffile. Or other sources with `[install]`: archives (`.tar.gz`, `.tar.xz`, `.zip`) are extracted, a `.bz2` file is decompressed, any other file is a program downloaded as is (executable, under its own name). `"/usr/bin/eza" = "eza"`: installed path (absolute, under `/usr/`, or a drop-in under `/etc`) = path inside the sources (relative, no `..`); a folder is copied whole, its links kept inside it. `[links]`: `"/usr/bin/nvim" = "/usr/lib/neovim/bin/nvim"`, a link under `/usr/` to a path the recipe installs. `[scripts]` as above, except with several vendor packages. `packages`: Debian packages it needs at run time; for a vendor .deb, added to its `Depends` (what the vendor's miss) |
| `vendor-repository` | `repository` (a file in `repositories/`, below), `packages`. Built as `dovy-<name>`, depending on the packages and on `dovy-repo-<repository>` |
| `testing-rebuild` | `source-package` (Debian testing's); one `[[source]]`: its `.dsc` (`url`, `sha256`), whose files dovy checks against it; built with `dpkg-buildpackage` against stable (and backports if required), without network; `packages` as for `upstream-build`; `build.sh` only if the default rebuild needs help |
| `setup` | `packages` (Debian; `name:i386` for 32-bit, which implies `requires = ["i386"]`), `backports = true` to pin them to backports (implies `backports`), `[[file]]` drop-ins (`path`, `content`); `[scripts]` for what files cannot do, e.g. restarting a service |
| `bundle` | `members` (recipes): installed with the bundle as recipes of their own, each removable; the bundle's package recommends them. A member whose other half is installed is skipped. New members come with `upgrade`. `packages` (Debian; `name:i386` implies `requires = ["i386"]`): the bundle's own, which it depends on |
| `local-build` | built from files the user has, not downloaded: `[local]` `path` (a folder under the home, `~/...`) and `match` (file name patterns, case ignored, e.g. `["*.ttf"]`). dovy copies the matching regular files, as the user, into the sources, keeping their sub-folders, and runs `build.sh` in the sandbox, without the network; the folder is only read. `build-depends` and `packages` as for `upstream-build`. The package's version is the recipe's plus when those files last changed (`1+20261120153000`), so files added, changed or removed make a newer one, which `upgrade` builds. With no matching file the recipe is not available; once installed, it is kept as it is |

## Package names

`upstream-build`, `upstream-binary`, `testing-rebuild` and `local-build`
build a package named after the recipe (`steam`). `setup`, `vendor-repository` and
`bundle` build `dovy-<name>` (`dovy-firefox`), so they never clash with
the packages they bring; a name already starting with `dovy-` is kept
(`dovy-defaults`). Every package records the catalog release it was built
from (`X-Dovy-Release`), for `show --diff`. A same-name replacement ships
a pin to dovy's repository at 1001, so Debian's newer version never
displaces it.

## Checks

Run on every catalog load, and by maintainers before review. Check 3 runs
for maintainers only: on a user's machine, packages from their own extra
repositories would refuse the whole catalog.

1. Valid TOML; no unknown fields; required fields present; name matches folder.
2. Every `[[source]]` has a 64-character sha256.
3. A name Debian stable already uses is listed in `replaces`.
4. `backports`/pin package lists name exact packages: no `*`.
5. `network` is given when `build.sh` uses the network (reviewed by hand).
6. `depends`, `conflicts`, `successor`, `members` name recipes that exist;
   `conflicts` go both ways; no dependency cycles.
7. `[[file]]` paths are drop-ins under `/etc` (`*.d/` folders, or tuned's
   override `/etc/tuned/profiles/<name>/tuned.conf`), never in
   home folders.
8. A vendor-repository recipe names a repository that exists.

A catalog with any failing recipe is refused as a whole.

## Repositories

`repositories/<name>.toml`, shared by the recipes that name it.

| Field | Meaning |
|---|---|
| `name` | equals the file name |
| `uri`, `suite`, `components` | the apt source; `uri` and `key-url` are https; a flat repository has a `suite` ending in `/` and no `components` |
| `key-url` | where dovy fetches the key, live, at install |
| `fingerprints` | every primary key in the key file; the file must hold exactly these |
| `maintainer` | who keeps it updated |
| `[[file]]` | only `/etc/default/<name>`, to configure the vendor's own scripts |
| `pin` | `false`: no pin; the vendor's packages may replace Debian's, by their own relations (NVIDIA only) |
| `repack` | `true`: never given to apt; each recipe's package is downloaded from it, repacked with the recipe's `[scripts]` and served locally. The recipe's first package is its own name; any after it are Debian packages the vendor's `Depends` miss, added to them. Its `version` is the version reviewed, the minimum dovy accepts |

One repository per host. dovy builds `dovy-repo-<name>`: the key in
binary form (`/usr/share/keyrings/dovy-<name>.pgp`), the source, the
files, and a pin: the host at 1, the packages of every installed recipe
using it at 100. It is rebuilt as those recipes come and go, and goes with
the last one.

## Example

```toml
name = "steam"
description = "Valve's Steam client"
kind = "upstream-binary"
version = "1.0.0.86"
maintainer = "hmwassim"
debian = [13]
requires = ["i386", "components"]

[[source]]
url = "https://repo.steampowered.com/steam/archive/stable/steam_1.0.0.86.tar.gz"
sha256 = "<64 hex characters>"
```
