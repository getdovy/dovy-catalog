# Contributing

Recipes run as root on other people's machines, so every change is
reviewed and tested before it reaches anyone. Asking for a recipe in an
issue is the easy path; a pull request takes a virtual machine and some
care.

## What belongs

- Software Debian stable lacks, or a newer version than it ships.
- System setup: backports, firmware, drivers, kernels, tuning.
- Proprietary software is fine; recipes point to the vendor's own files.

Not accepted: what Debian stable already has at the same or a newer
version; downloads without a fixed version; software that needs a script
piped to a shell.

## A recipe

Format and checks: [docs/recipe-format.md](docs/recipe-format.md). A
minimal one:

```toml
name = "example"
description = "One line, no final period"
kind = "upstream-binary"
version = "1.2.3"
maintainer = "your-github-name"
debian = [13]

[[source]]
url = "https://example.org/releases/1.2.3/example-1.2.3-linux-amd64.tar.gz"
sha256 = "<64 hex characters>"

[install]
"/usr/bin/example" = "example-1.2.3/example"
```

- Pin an exact version and its sha256; never "latest".
- Read the vendor's maintainer scripts, and say in the pull request what
  they do.
- You become the recipe's `maintainer`: you keep it updated.

## Testing

In a Debian 13 virtual machine with KDE, never on your own system: the
test installs and removes as root, and leaves a test release behind.

1. Install dovy from its
   [release page](https://github.com/getdovy/dovy/releases/latest), and the
   tools to build it:

   ```sh
   sudo apt install git golang-go make
   ```

2. Clone your fork on your branch, and sign a test release with a key made
   for it:

   ```sh
   git clone -b <branch> https://github.com/<you>/dovy-catalog
   ssh-keygen -t ed25519 -N '' -f ~/.ssh/dovy-test
   cd dovy-catalog
   git -c gpg.format=ssh -c user.signingkey=$HOME/.ssh/dovy-test.pub \
       tag -s -m test "catalog-$(date -u +%Y.%m.%d).1"
   ```

3. Trust that key on this machine only:

   ```sh
   printf 'test namespaces="git" %s\n' "$(cat ~/.ssh/dovy-test.pub)" |
       sudo tee /etc/dovy/keys.d/test
   ```

4. Build dovy pointed at your clone:

   ```sh
   git clone https://github.com/getdovy/dovy
   make -C dovy CATALOG="$PWD/dovy-catalog"
   ```

5. Install, use the software, then remove it:

   ```sh
   ./dovy/dovy update
   ./dovy/dovy install <recipe>
   ./dovy/dovy remove <recipe>
   ```

   After a change to the recipe, delete the tag, tag again, and run
   `update`.

## Pull requests

Into `main`, from a branch of your fork. The template asks for:

1. why the recipe belongs;
2. where the software comes from;
3. what the vendor's scripts do, if any;
4. what you tested, and the dovy version.

A maintainer then tests it on a clean system before merging. Merged
changes reach users with the next catalog release.

Commits: `type(scope): summary`, for example
`feat(recipes): add example`.

By opening a pull request you agree that your contribution is licensed
under this repository's licence, GPL-3.0-or-later.
