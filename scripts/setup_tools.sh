#!/usr/bin/env bash
# repak(레거시 pak 추출/패킹 도구)을 tools/bin/ 에 설치한다.
# build-from-source 에 필요. 프리빌트 pak 만 쓸 경우 불필요.
set -euo pipefail

REPAK_VER="v0.2.3"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="$HERE/tools/bin"
mkdir -p "$BIN"

os="$(uname -s)"; arch="$(uname -m)"
case "$os-$arch" in
  Linux-x86_64)  asset="repak_cli-x86_64-unknown-linux-gnu.tar.xz" ;;
  Darwin-x86_64) asset="repak_cli-x86_64-apple-darwin.tar.xz" ;;
  Darwin-arm64)  asset="repak_cli-aarch64-apple-darwin.tar.xz" ;;
  *) echo "지원되지 않는 플랫폼: $os-$arch"
     echo "Windows 사용자는 WSL을 쓰거나 https://github.com/trumank/repak/releases 에서 직접 받으세요."
     exit 1 ;;
esac

url="https://github.com/trumank/repak/releases/download/${REPAK_VER}/${asset}"
echo "다운로드: $url"
tmp="$(mktemp -d)"
curl -sL --max-time 120 -o "$tmp/repak.tar.xz" "$url"
tar xf "$tmp/repak.tar.xz" -C "$tmp"
found="$(find "$tmp" -type f -name repak | head -1)"
cp "$found" "$BIN/repak"
chmod +x "$BIN/repak"
rm -rf "$tmp"
echo "설치 완료: $BIN/repak"
"$BIN/repak" --version
