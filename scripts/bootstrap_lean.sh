#!/usr/bin/env bash
set -euo pipefail
# Official Linux x86_64 Lean archive; exact version and bytes pinned.
base="${1:-$PWD/.toolchain}"
mkdir -p "$base"
archive="$base/lean-4.19.0-linux.tar.zst"
curl --fail --location --retry 2 --output "$archive" https://github.com/leanprover/lean4/releases/download/v4.19.0/lean-4.19.0-linux.tar.zst
printf '%s  %s\n' 6fe3ce97a58f44e2b3567d455b994eacec5bfe9ae7774f2a573444480ba813fe "$archive" | sha256sum -c -
tar --no-same-owner --zstd -xf "$archive" -C "$base"
if [[ -n "${GITHUB_PATH:-}" ]]; then
  printf '%s\n' "$base/lean-4.19.0-linux/bin" >> "$GITHUB_PATH"
fi
printf 'Lean installed: %s\n' "$base/lean-4.19.0-linux/bin"
