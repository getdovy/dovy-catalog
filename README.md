<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/getdovy/dovy-catalog/main/.github/logo/dovy-catalog-wordmark-dark.svg">
    <img alt="dovy-catalog" src="https://raw.githubusercontent.com/getdovy/dovy-catalog/main/.github/logo/dovy-catalog-wordmark.svg" height="64">
  </picture>
</p>

<p align="center">
  Signed recipes for dovy.<br>
  Not part of Debian.
</p>

## Overview

A recipe tells [dovy](https://github.com/getdovy/dovy) how to install one
piece of software on Debian stable: where it comes from, its exact version
and checksum, and what it needs. dovy builds a package from it on your
machine and installs it with apt.

Each release of this catalog is a signed tag, `catalog-YYYY.MM.DD.N`.
dovy uses the newest release it trusts and can read, and refuses anything
unsigned or changed.

## Recipes

What is available depends on your dovy version, so the list lives in dovy:

```sh
dovy update
dovy list
dovy show <recipe>
```

The catalog covers:

- software Debian stable lacks;
- newer versions of software Debian ships;
- system setup: backports, firmware, drivers, kernels, tuning.

A recipe for something Debian stable already has, at the same or a newer
version, is not accepted.

## Asking for a recipe

Open an issue with the
[recipe request](https://github.com/getdovy/dovy-catalog/issues/new?template=recipe-request.yml)
form. For a newer version of an existing recipe, use
[recipe update](https://github.com/getdovy/dovy-catalog/issues/new?template=recipe-update.yml);
for one that fails, [broken recipe](https://github.com/getdovy/dovy-catalog/issues/new?template=broken-recipe.yml).

## Contributing

Recipes come as pull requests, tested in a Debian stable virtual machine:
[CONTRIBUTING.md](CONTRIBUTING.md). The format:
[docs/recipe-format.md](docs/recipe-format.md).

## Layout

| Path | Holds |
|---|---|
| `recipes/<name>/` | `recipe.toml`, and `build.sh` for recipes that build |
| `repositories/` | vendor apt repositories, shared by recipes |
| `catalog.toml` | the oldest dovy that can read this release |
| `docs/` | the recipe format |

## Licence

GPL-3.0-or-later: [LICENSE](LICENSE). Name and logo:
[TRADEMARKS.md](TRADEMARKS.md). Recipes describe where software comes
from; dovy never redistributes it.
