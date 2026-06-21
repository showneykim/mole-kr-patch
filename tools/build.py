#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
M.O.L.E 한국어 패치 빌더 (build-from-source)

당신이 소유한 M.O.L.E 설치본에서 원본 .pak을 읽어 한국어 패치 pak
(Mole-Windows_P.pak)을 생성한다. 원본 게임 에셋은 저장소에 포함되지 않으며,
오직 우리의 번역 데이터(data/)와 폰트(fonts/)만 사용한다.

필요한 것:
  - Python 3.8+
  - repak (https://github.com/trumank/repak) — scripts/setup_tools.sh 로 설치 가능
사용 예:
  python tools/build.py --game "/path/to/steamapps/common/M.O.L.E"
  python tools/build.py --game "C:/Program Files (x86)/Steam/steamapps/common/M.O.L.E" --install
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import locres  # noqa: E402

# repak은 파일을 병렬(rayon)로 패킹해 데이터 오프셋 순서가 매번 달라진다(비결정적).
# 단일 스레드로 강제하면 같은 입력 → 같은 pak(바이트 동일)이 되어 빌드가 재현 가능해진다.
REPAK_ENV = {**os.environ, "RAYON_NUM_THREADS": "1"}

GAME_LOCRES   = "Mole/Content/Localization/Game/ja/Game.locres"
ENGINE_LOCRES = "Engine/Content/Localization/Engine/ja/Engine.locres"
FONT_DIR      = "Mole/Content/Drift/Art/Fonts"
# 게임이 사용하는 커스텀 폰트 6종 — 모두 동일한 한글 폰트로 교체한다.
FONTS = [
    "DotGothic16-Regular", "ZLabsBitmap_12px_CN", "ZLabsBitmap_12px_HC",
    "ZLabsBitmap_12px_HC_FALLBACK", "MonocraftUpdated", "small_adventure_inverted_font",
]

def log(msg): print(f"[build] {msg}")

def find_repak(explicit=None):
    if explicit and os.path.exists(explicit):
        return explicit
    env = os.environ.get("REPAK")
    if env and os.path.exists(env):
        return env
    # 저장소 tools/bin, PATH 순으로 탐색
    for cand in [os.path.join(HERE, "bin", "repak"),
                 os.path.join(HERE, "bin", "repak.exe"),
                 shutil.which("repak")]:
        if cand and os.path.exists(cand):
            return cand
    sys.exit("repak 를 찾을 수 없습니다. scripts/setup_tools.sh 를 실행하거나 --repak 로 경로를 지정하세요.")

def find_game_pak(game_path):
    """게임 루트/Paks 디렉터리 어디를 주든 Mole-Windows.pak 을 찾는다."""
    if os.path.isfile(game_path) and game_path.endswith(".pak"):
        return game_path
    for base, _dirs, files in os.walk(game_path):
        if "Mole-Windows.pak" in files:
            return os.path.join(base, "Mole-Windows.pak")
    sys.exit(f"Mole-Windows.pak 을 찾을 수 없습니다: {game_path}")

def repak_info(repak, pak):
    out = subprocess.check_output([repak, "info", pak], text=True, stderr=subprocess.STDOUT)
    info = {}
    for line in out.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            info[k.strip().lower()] = v.strip()
    version = info.get("version", "V11")
    mount = info.get("mount point", "../../../")
    seed_raw = info.get("path hash seed", "0")
    m = re.search(r"([0-9A-Fa-f]{6,})", seed_raw)
    seed = int(m.group(1), 16) if m else 0
    return version, mount, seed

def apply_locres(src_path, dst_path, ja2ko):
    """src locres 를 읽어 ja->ko 매핑을 적용하고 dst 에 저장. 적용/미적용 수 반환."""
    doc = locres.load(src_path)
    hit = miss = 0
    for s in doc["strings"]:
        ja = s[0]
        if ja in ja2ko:
            s[0] = ja2ko[ja]
            s[1] = "utf16"
            hit += 1
        else:
            miss += 1
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    open(dst_path, "wb").write(locres.dump(doc))
    return hit, miss

def main():
    ap = argparse.ArgumentParser(description="M.O.L.E 한국어 패치 빌더")
    ap.add_argument("--game", required=True, help="M.O.L.E 설치 폴더 또는 Paks 경로")
    ap.add_argument("--repak", help="repak 실행파일 경로 (미지정 시 자동 탐색)")
    ap.add_argument("--font", default=os.path.join(ROOT, "fonts", "Galmuri11.ttf"),
                    help="한글 폰트 TTF (기본: fonts/Galmuri11.ttf)")
    ap.add_argument("--output", default=os.path.join(ROOT, "release", "Mole-Windows_P.pak"))
    ap.add_argument("--install", action="store_true", help="빌드 후 게임 Paks 폴더에 바로 복사")
    args = ap.parse_args()

    repak = find_repak(args.repak)
    game_pak = find_game_pak(args.game)
    paks_dir = os.path.dirname(game_pak)
    log(f"repak     = {repak}")
    log(f"원본 pak  = {game_pak}")

    version, mount, seed = repak_info(repak, game_pak)
    log(f"pak 정보  = version={version} mount={mount} seed=0x{seed:08X}")

    translations = json.load(open(os.path.join(ROOT, "data", "translations.json"), encoding="utf-8"))
    engine_keys  = json.load(open(os.path.join(ROOT, "data", "engine_keys.json"), encoding="utf-8"))

    with tempfile.TemporaryDirectory() as tmp:
        extract = os.path.join(tmp, "extract")
        stage = os.path.join(tmp, "stage")
        log("원본 pak 추출 중...")
        subprocess.run([repak, "unpack", game_pak, "-o", extract], check=True,
                       stdout=subprocess.DEVNULL)

        # 1) Game.locres (본문 1300)
        hit, miss = apply_locres(os.path.join(extract, GAME_LOCRES),
                                 os.path.join(stage, GAME_LOCRES), translations)
        log(f"Game.locres  : {hit} 적용 / {miss} 미적용")
        # 2) Engine.locres (키 이름)
        ehit, emiss = apply_locres(os.path.join(extract, ENGINE_LOCRES),
                                   os.path.join(stage, ENGINE_LOCRES), engine_keys)
        log(f"Engine.locres: {ehit} 적용 (키 이름)")
        # 3) 폰트 6종을 한글 폰트로 교체
        os.makedirs(os.path.join(stage, FONT_DIR), exist_ok=True)
        for f in FONTS:
            shutil.copy(args.font, os.path.join(stage, FONT_DIR, f + ".ufont"))
        log(f"폰트 교체    : {len(FONTS)}종 <- {os.path.basename(args.font)}")

        # 4) 패치 pak 패킹 (원본과 동일한 version/mount/seed)
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        subprocess.run([repak, "pack", stage, args.output,
                        "--version", version, "--mount-point", mount,
                        "--path-hash-seed", str(seed)], check=True,
                       stdout=subprocess.DEVNULL, env=REPAK_ENV)
    log(f"완료 -> {args.output}")

    if args.install:
        dst = os.path.join(paks_dir, "Mole-Windows_P.pak")
        shutil.copy(args.output, dst)
        log(f"설치 완료 -> {dst}")
        log("게임을 완전히 종료 후 재실행하고, 언어를 '日本語'로 설정하세요.")

if __name__ == "__main__":
    main()
