#!/usr/bin/env bash
# Pinned upstream Linux x86_64 release, verified before extraction.
set -euo pipefail
destination="${1:?Usage: bash scripts/bootstrap_mdbook.sh INSTALL_DIR}"
version=0.4.52
expected=c0b903f01dd8f4edc644372ad2b80b1fdddd12552d37b6a098657cbd8eddd768
if [[ "$(uname -s)" != Linux || "$(uname -m)" != x86_64 ]]; then
    echo 'This installer supports Linux x86_64. Install mdbook 0.4.52 for your platform.' >&2
    exit 1
fi
mkdir -p "$destination"
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
curl --fail --location --retry 3 --proto '=https' --tlsv1.2 \
    "https://github.com/rust-lang/mdBook/releases/download/v${version}/mdbook-v${version}-x86_64-unknown-linux-gnu.tar.gz" \
    --output "$scratch/mdbook.tar.gz"
printf '%s  %s\n' "$expected" "$scratch/mdbook.tar.gz" | sha256sum --check --status
tar -xzf "$scratch/mdbook.tar.gz" -C "$scratch" mdbook
install -m 755 "$scratch/mdbook" "$destination/mdbook"
"$destination/mdbook" --version
