#!/usr/bin/env python3
"""
ツアマスカードリストから画像とメタデータをダウンロードするスクリプト。
実行後、dist/card_metadata.json と dist/card_images/*.webp が生成される。

使用方法:
    uv run python scripts/download_cards.py [--limit N] [--workers N]
"""

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

BASE_URL = "https://bandainamco-am.co.jp/am/vg/idolmaster-tours"
CARD_JSON_URL = f"{BASE_URL}/cardlist/card_20260423.json?v1.1"
IMAGE_BASE_URL = f"{BASE_URL}/images/cardlist/cards"

REPO_ROOT = Path(__file__).parent.parent
DIST_DIR = REPO_ROOT / "dist"
IMAGE_CACHE_DIR = DIST_DIR / "card_images"
METADATA_JSON = DIST_DIR / "card_metadata.json"

SERIES_PREFIX: dict[str, str] = {
    "series-1":     "01",
    "series-2":     "02",
    "series-3":     "03",
    "series-4":     "04",
    "series-5":     "05",
    "series-pm":    "06",
    "series-cp":    "07",
    "series-ex":    "08",
    "series-1test": "09",
    "series-2test": "10",
}

TYPE_MAP: dict[str, str] = {
    "コスチューム": "costume",
    "アクセサリー": "accessory",
    "サポート":     "support",
    "SPアピール":   "sp_appeal",
    "演出セット":   "perf_set",
}


def build_number_to_id(all_cards: list[dict]) -> dict[str, str]:
    """カード番号 → TOML ID のマッピングを構築する（シリーズ内ランク方式）。"""
    from collections import defaultdict
    series_cards: dict[str, list[dict]] = defaultdict(list)
    for c in all_cards:
        series_cards[c["series_id"]].append(c)
    mapping: dict[str, str] = {}
    for series_id, s_cards in series_cards.items():
        s_cards.sort(key=lambda x: int(x["number"]))
        prefix = SERIES_PREFIX.get(series_id, "XX")
        for rank, card in enumerate(s_cards, 1):
            mapping[card["number"]] = f"IMT-{prefix}-{rank:03d}"
    return mapping


def download_image(card: dict) -> tuple[str, bool]:
    """カード裏面画像をダウンロード。(number, success) を返す。"""
    number = card["number"]
    image_path = IMAGE_CACHE_DIR / f"{number}_u.webp"
    if image_path.exists():
        return number, True
    url = f"{IMAGE_BASE_URL}/{number}_u.webp"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        image_path.write_bytes(resp.content)
        return number, True
    except requests.RequestException as e:
        print(f"  [ERROR] {number}: {e}", file=sys.stderr)
        return number, False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()

    print("カードリスト JSON を取得中...")
    resp = requests.get(CARD_JSON_URL, timeout=15)
    resp.raise_for_status()
    all_cards: list[dict] = resp.json()["cardlist"]
    print(f"  {len(all_cards)} 件のカードを確認")

    if args.limit > 0:
        all_cards = all_cards[: args.limit]

    IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    number_to_id = build_number_to_id(all_cards)

    # メタデータを保存
    metadata = {
        number_to_id[c["number"]]: {
            "number":    c["number"],
            "idol":      c["name"],
            "rarity":    c["rarity"],
            "type_jp":   c["type"],
            "type":      TYPE_MAP.get(c["type"], "unknown"),
            "series_id": c["series_id"],
            "image_path": str(IMAGE_CACHE_DIR / f"{c['number']}_u.webp"),
        }
        for c in all_cards
    }
    METADATA_JSON.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  メタデータ保存: {METADATA_JSON}")

    # 画像ダウンロード
    already = sum(1 for c in all_cards if (IMAGE_CACHE_DIR / f"{c['number']}_u.webp").exists())
    need = [c for c in all_cards if not (IMAGE_CACHE_DIR / f"{c['number']}_u.webp").exists()]
    print(f"\n画像ダウンロード: 既存 {already} 件 / 未取得 {len(need)} 件")

    if need:
        ok = failed = 0
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            futures = {ex.submit(download_image, c): c for c in need}
            for i, fut in enumerate(as_completed(futures), 1):
                number, success = fut.result()
                if success:
                    ok += 1
                else:
                    failed += 1
                if i % 50 == 0:
                    print(f"  {i}/{len(need)} ... 成功 {ok} 失敗 {failed}")
        print(f"  完了: 成功 {ok} / 失敗 {failed}")

    total = sum(1 for c in all_cards if (IMAGE_CACHE_DIR / f"{c['number']}_u.webp").exists())
    print(f"\n画像キャッシュ合計: {total} 件")
    print(f"次のステップ: claude Code で scripts/scrape_card_texts.py を実行してOCRを行う")


if __name__ == "__main__":
    main()
