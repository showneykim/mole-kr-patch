# M.O.L.E Korean Patch 🇰🇷

[한국어](README.md) · Unofficial fan translation

An **unofficial fan-made Korean translation** for the Steam psychological-horror game
**[M.O.L.E](https://store.steampowered.com/app/4064510/MOLE/)** (by Z Labs). The game ships
without official Korean support, so this patch works by **overwriting the unused Japanese (日本語)
locale slot with Korean**. Select Japanese in-game and the UI appears in Korean.

> ⚠️ Unofficial patch. For use only with a **legally owned copy** of the game. See [DISCLAIMER.md](DISCLAIMER.md).

---

## ⚡ Quick install (prebuilt)

1. Download **`Mole-Windows_P.pak`** from [GitHub Releases](../../releases).
2. Drop it into your game folder:
   ```
   ...\steamapps\common\M.O.L.E\Windows\Mole\Content\Paks\
   ```
3. Launch the game and choose **Settings → Language → 日本語 (Japanese)**.
4. The UI is now in Korean. 🎉

**To uninstall**, delete the `Mole-Windows_P.pak` file. It never overwrites originals.

```
SHA256  4fca7ae0c9d9c07cc96054adf472f58ff4af0b65553257aa79b203637a8a859a
```

## 🔧 Build from source

This repository contains **no original game assets**. The build reads the original files from your
own installation. The build is **deterministic**: with the same game version (build 1.1.5) and font,
it reproduces the prebuilt release **byte-for-byte**, matching its SHA256. (`build.py` runs repak
single-threaded to guarantee reproducibility.)

Requires Python 3.8+ and [repak](https://github.com/trumank/repak).

```bash
bash scripts/setup_tools.sh                                   # installs repak (Linux/macOS/WSL)
python tools/build.py --game "/path/to/steamapps/common/M.O.L.E" --install
```

The builder extracts the legacy `Mole-Windows.pak`, applies the translations in `data/` to
`Game.locres` and `Engine.locres`, swaps the 6 custom pixel fonts for a Hangul-capable font, and
repacks with the original `version/mount/seed`.

## How it works

Translate the game text (`Game.locres`, 1300 strings) and the engine key names (`Engine.locres`,
115 entries) into Korean, replace the game's 6 custom pixel fonts with one that contains Hangul
(Galmuri11), and ship it all in a higher-priority `_P.pak` overlay — no original files are modified.
The full reverse-engineering, font, translation, and verification story lives in [`docs/`](docs/).

## Facts

| | |
|---|---|
| Game | M.O.L.E (Steam app 4064510, Z Labs) |
| Engine | Unreal Engine 5 (IoStore + legacy pak) |
| Method | overwrite the Japanese locale slot |
| Translated | 1300 game strings + 115 engine key names |
| Fonts | 6 custom fonts → Galmuri11 |
| Artifact | `Mole-Windows_P.pak` (~35 MB) |

## License · Credits

- Code & tooling (`tools/`, `scripts/`): [MIT](LICENSE)
- Translation, docs, build artifact: see [DISCLAIMER.md](DISCLAIMER.md) (unofficial; requires game ownership; no game assets included)
- Font: [Galmuri](https://galmuri.quiple.dev) © quiple — SIL Open Font License 1.1
- Tools: [repak](https://github.com/trumank/repak) / [retoc](https://github.com/trumank/retoc) by trumank

Not affiliated with Z Labs or the M.O.L.E publisher.
