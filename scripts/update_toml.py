#!/usr/bin/env python3
"""
dist/card_texts_extracted.json の内容を card_data/*.toml に反映するスクリプト。

使用方法:
    uv run python scripts/update_toml.py
"""

import json
import sys
from pathlib import Path

import toml

REPO_ROOT = Path(__file__).parent.parent
CARD_DATA_DIR = REPO_ROOT / "card_data"
DIST_DIR = REPO_ROOT / "dist"
EXTRACTED_JSON = DIST_DIR / "card_texts_extracted.json"

TYPE_TO_FILE: dict[str, Path] = {
    "costume":   CARD_DATA_DIR / "costume.toml",
    "accessory": CARD_DATA_DIR / "accessory.toml",
    "support":   CARD_DATA_DIR / "support.toml",
    "sp_appeal": CARD_DATA_DIR / "sp_appeal.toml",
    "perf_set":  CARD_DATA_DIR / "perf_set.toml",
}


def load_existing_toml() -> dict[str, dict]:
    existing: dict[str, dict] = {}
    for toml_file in CARD_DATA_DIR.glob("*.toml"):
        try:
            data = toml.load(toml_file)
            for card in data.get("card", []):
                existing[card["id"]] = card
        except Exception as e:
            print(f"  [WARN] {toml_file.name}: {e}", file=sys.stderr)
    return existing


def build_card_entry(toml_id: str, data: dict, existing: dict[str, dict]) -> dict:
    card_type = data.get("type", "unknown")

    # 既存TOMLを基にしつつ、抽出データで上書き
    card: dict = dict(existing.get(toml_id, {}))

    # 基本フィールド
    card["id"] = toml_id
    card["name"] = data.get("card_name") or card.get("name", "")
    card["idol"] = data.get("idol") or card.get("idol", "")
    card["rarity"] = data.get("rarity") or card.get("rarity", "")
    card["text"] = data.get("text") or card.get("text", "")
    card["type"] = card_type
    if data.get("subject"):
        card["subject"] = data["subject"]

    # タイプ別フィールド
    if card_type == "costume" and data.get("appeal"):
        card["appeal"] = data["appeal"]
    elif card_type == "accessory" and data.get("body_part"):
        card["body_part"] = data["body_part"]
    elif card_type == "support" and data.get("support_skill"):
        card["support_skill"] = data["support_skill"]
    elif card_type == "sp_appeal" and data.get("sp_appeal"):
        card["sp_appeal"] = data["sp_appeal"]

    return card


def main() -> None:
    if not EXTRACTED_JSON.exists():
        print(f"エラー: {EXTRACTED_JSON} が見つかりません。先にOCRを実行してください。", file=sys.stderr)
        sys.exit(1)

    extracted: dict[str, dict] = json.loads(EXTRACTED_JSON.read_text(encoding="utf-8"))
    print(f"抽出済みデータ: {len(extracted)} 件")

    existing = load_existing_toml()
    print(f"既存TOMLカード: {len(existing)} 件")

    cards_by_type: dict[str, list[dict]] = {t: [] for t in TYPE_TO_FILE}

    for toml_id, data in extracted.items():
        card_type = data.get("type", "unknown")
        if card_type not in cards_by_type:
            print(f"  [SKIP] 未対応タイプ {card_type}: {toml_id}")
            continue
        card = build_card_entry(toml_id, data, existing)
        cards_by_type[card_type].append(card)

    for card_type, cards in cards_by_type.items():
        if not cards:
            continue
        toml_file = TYPE_TO_FILE[card_type]
        cards_sorted = sorted(cards, key=lambda c: c.get("id", ""))
        toml_file.write_text(
            toml.dumps({"card": cards_sorted}),
            encoding="utf-8",
        )
        print(f"  書き込み: {toml_file.name} ({len(cards_sorted)} 件)")

    print("\n完了！")


if __name__ == "__main__":
    main()
