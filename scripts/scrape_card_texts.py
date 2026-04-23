#!/usr/bin/env python3
"""
ツアマスカードリストサイトからカード裏面画像を取得し、
claude CLIを使ってテキストを抽出してTOMLファイルに書き出すスクリプト。

使用方法:
    uv run python scripts/scrape_card_texts.py [--limit N] [--workers N]

オプション:
    --limit N    処理するカード数の上限（デフォルト: 全件）
    --workers N  並列処理数（デフォルト: 3）
"""

import argparse
import json
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
import toml

BASE_URL = "https://bandainamco-am.co.jp/am/vg/idolmaster-tours"
CARD_JSON_URL = f"{BASE_URL}/cardlist/card_20260423.json?v1.1"
IMAGE_BASE_URL = f"{BASE_URL}/images/cardlist/cards"

REPO_ROOT = Path(__file__).parent.parent
CARD_DATA_DIR = REPO_ROOT / "card_data"
DIST_DIR = REPO_ROOT / "dist"
IMAGE_CACHE_DIR = DIST_DIR / "card_images"
EXTRACTED_JSON = DIST_DIR / "card_texts_extracted.json"

# シリーズID → (TOMLの2桁プレフィックス, 開始カード番号のオフセット)
# 例: series-1 の番号0001は offset=0 なので within_series=1 → IMT-01-001
SERIES_CONFIG: dict[str, tuple[str, int]] = {
    "series-1":   ("01", 0),
    "series-2":   ("02", 106),
    "series-3":   ("03", 212),
    "series-4":   ("04", 309),
    "series-5":   ("05", 415),
    "promotion":  ("06", 505),
    "campaign":   ("07", 513),
    "extra":      ("08", 545),
    "loc-test-1": ("09", 565),
    "loc-test-2": ("10", 594),
}

TYPE_MAP: dict[str, str] = {
    "コスチューム": "costume",
    "アクセサリー": "accessory",
    "サポート":     "support",
    "SPアピール":   "sp_appeal",
    "演出セット":   "perf_set",
}

TYPE_TO_FILE: dict[str, Path] = {
    "costume":   CARD_DATA_DIR / "costume.toml",
    "accessory": CARD_DATA_DIR / "accessory.toml",
    "support":   CARD_DATA_DIR / "support.toml",
    "sp_appeal": CARD_DATA_DIR / "sp_appeal.toml",
    "perf_set":  CARD_DATA_DIR / "perf_set.toml",
}

OCR_PROMPT_TEMPLATE = """\
以下のパスにあるアーケードカードの裏面画像を Read ツールで読み込み、内容を解析してください。
ファイルパス: {image_path}

以下のフィールドを含む JSON オブジェクトのみを返してください（説明文や追加テキストは不要）:

{{
  "card_name": "カード名（カード上部に記載の名称）",
  "text": "カードのフレーバーテキストまたはスキル説明文（カードに書かれているメインのテキスト）",
  "subject": "対象（everyone / female / male / unique のいずれか、記載がなければ null）",
  "appeal": {{"vocal": 数値, "dance": 数値, "visual": 数値}},
  "body_part": "アクセサリーの装着部位（head/face/hand/body/waist/leg、アクセサリー以外は null）",
  "support_skill": {{"live_type": ["rhythm" または "create"], "description": ["スキル説明文"]}},
  "sp_appeal": {{"effect": ["効果説明文"]}}
}}

注意:
- appeal はコスチュームカードのみ、それ以外は null
- body_part はアクセサリーカードのみ、それ以外は null
- support_skill はサポートカードのみ、それ以外は null
- sp_appeal は SP アピールカードのみ、それ以外は null
- JSON のみ返すこと（コードブロック記法も不要）
"""

JSON_SCHEMA = json.dumps({
    "type": "object",
    "properties": {
        "card_name":     {"type": "string"},
        "text":          {"type": "string"},
        "subject":       {"type": ["string", "null"]},
        "appeal":        {"type": ["object", "null"]},
        "body_part":     {"type": ["string", "null"]},
        "support_skill": {"type": ["object", "null"]},
        "sp_appeal":     {"type": ["object", "null"]},
    },
    "required": ["card_name", "text"],
})


def get_toml_id(card: dict) -> str:
    series_id = card.get("series_id", "")
    config = SERIES_CONFIG.get(series_id)
    if not config:
        return f"IMT-XX-{int(card['number']):03d}"
    prefix, offset = config
    within_series = int(card["number"]) - offset
    return f"IMT-{prefix}-{within_series:03d}"


def download_image(number: str) -> Path | None:
    IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    image_path = IMAGE_CACHE_DIR / f"{number}_u.webp"
    if image_path.exists():
        return image_path
    url = f"{IMAGE_BASE_URL}/{number}_u.webp"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        image_path.write_bytes(resp.content)
        return image_path
    except requests.RequestException as e:
        print(f"  [ERROR] 画像ダウンロード失敗 {url}: {e}", file=sys.stderr)
        return None


def extract_with_claude(image_path: Path) -> dict | None:
    prompt = OCR_PROMPT_TEMPLATE.format(image_path=image_path.absolute())
    try:
        result = subprocess.run(
            [
                "claude", "-p", prompt,
                "--allowed-tools", "Read",
                "--add-dir", str(IMAGE_CACHE_DIR),
                "--output-format", "json",
                "--no-session-persistence",
                "--bare",
                "--json-schema", JSON_SCHEMA,
            ],
            capture_output=True,
            text=True,
            timeout=90,
        )
    except subprocess.TimeoutExpired:
        print(f"  [ERROR] claude タイムアウト: {image_path.name}", file=sys.stderr)
        return None

    if result.returncode != 0:
        print(f"  [ERROR] claude 終了コード {result.returncode}: {result.stderr[:200]}", file=sys.stderr)
        return None

    try:
        output = json.loads(result.stdout)
        # --output-format json では {"result": "...", ...} 形式で返る
        raw = output.get("result", "")
        if isinstance(raw, dict):
            return raw
        return json.loads(raw)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"  [ERROR] JSON パース失敗 ({image_path.name}): {e}", file=sys.stderr)
        print(f"  stdout: {result.stdout[:300]}", file=sys.stderr)
        return None


def load_existing_toml() -> dict[str, dict]:
    existing: dict[str, dict] = {}
    for toml_file in CARD_DATA_DIR.glob("*.toml"):
        try:
            data = toml.load(toml_file)
            for card in data.get("card", []):
                existing[card["id"]] = card
        except Exception as e:
            print(f"  [WARN] {toml_file.name} 読み込み失敗: {e}", file=sys.stderr)
    return existing


def load_extracted() -> dict[str, dict]:
    if EXTRACTED_JSON.exists():
        return json.loads(EXTRACTED_JSON.read_text(encoding="utf-8"))
    return {}


def save_extracted(extracted: dict[str, dict]) -> None:
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACTED_JSON.write_text(
        json.dumps(extracted, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def process_card(card: dict, extracted: dict, lock_file: Path) -> tuple[str, dict | None]:
    """1枚のカードを処理して (toml_id, ocr_result) を返す。"""
    toml_id = get_toml_id(card)

    if toml_id in extracted:
        return toml_id, None  # スキップ

    image_path = download_image(card["number"])
    if not image_path:
        return toml_id, None

    ocr_result = extract_with_claude(image_path)
    return toml_id, ocr_result


def build_card_entry(
    toml_id: str,
    data: dict,
    existing: dict[str, dict],
) -> dict:
    """抽出データと既存TOMLから最終的なカードエントリを構築する。"""
    card_type = data.get("type", "unknown")

    if toml_id in existing:
        card = dict(existing[toml_id])
        if data.get("text"):
            card["text"] = data["text"]
        return card

    # 新規カード
    card: dict = {
        "id": toml_id,
        "name": data.get("card_name", ""),
        "idol": data.get("idol", ""),
        "rarity": data.get("rarity", ""),
        "text": data.get("text", ""),
        "type": card_type,
    }
    if data.get("subject"):
        card["subject"] = data["subject"]

    if card_type == "costume" and data.get("appeal"):
        card["appeal"] = data["appeal"]
    elif card_type == "accessory" and data.get("body_part"):
        card["body_part"] = data["body_part"]
    elif card_type == "support" and data.get("support_skill"):
        card["support_skill"] = data["support_skill"]
    elif card_type == "sp_appeal" and data.get("sp_appeal"):
        card["sp_appeal"] = data["sp_appeal"]

    return card


def write_toml_files(cards_by_type: dict[str, list[dict]]) -> None:
    for card_type, cards in cards_by_type.items():
        if not cards:
            continue
        toml_file = TYPE_TO_FILE.get(card_type)
        if not toml_file:
            print(f"  [WARN] 未知のタイプ {card_type} → スキップ")
            continue
        cards_sorted = sorted(cards, key=lambda c: c.get("id", ""))
        toml_file.write_text(
            toml.dumps({"card": cards_sorted}),
            encoding="utf-8",
        )
        print(f"  書き込み完了: {toml_file.name} ({len(cards_sorted)} 件)")


def main() -> None:
    parser = argparse.ArgumentParser(description="ツアマスカードテキストスクレイパー")
    parser.add_argument("--limit", type=int, default=0, help="処理上限数（0=全件）")
    parser.add_argument("--workers", type=int, default=3, help="並列処理数")
    args = parser.parse_args()

    print("カードリスト JSON を取得中...")
    resp = requests.get(CARD_JSON_URL, timeout=15)
    resp.raise_for_status()
    all_cards: list[dict] = resp.json()["cardlist"]
    print(f"  {len(all_cards)} 件のカードを確認")

    if args.limit > 0:
        all_cards = all_cards[: args.limit]
        print(f"  --limit により {args.limit} 件に絞り込み")

    existing_toml = load_existing_toml()
    extracted = load_extracted()
    print(f"  既存TOMLカード: {len(existing_toml)} 件")
    print(f"  抽出済みキャッシュ: {len(extracted)} 件")

    remaining = [c for c in all_cards if get_toml_id(c) not in extracted]
    print(f"  未処理: {len(remaining)} 件\n")

    if remaining:
        processed = 0
        failed = 0

        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {
                executor.submit(process_card, card, extracted, EXTRACTED_JSON): card
                for card in remaining
            }
            for future in as_completed(futures):
                card = futures[future]
                toml_id = get_toml_id(card)
                try:
                    _, ocr_result = future.result()
                except Exception as e:
                    print(f"  [ERROR] {toml_id}: {e}", file=sys.stderr)
                    failed += 1
                    continue

                if ocr_result is None:
                    if toml_id not in extracted:
                        failed += 1
                    continue

                extracted[toml_id] = {
                    "number":   card["number"],
                    "idol":     card["name"],
                    "rarity":   card["rarity"],
                    "type_jp":  card["type"],
                    "type":     TYPE_MAP.get(card["type"], "unknown"),
                    "series_id": card["series_id"],
                    **ocr_result,
                }
                save_extracted(extracted)
                processed += 1
                text_preview = ocr_result.get("text", "")[:40]
                print(
                    f"  [{processed + len(extracted) - len(remaining):>3}/"
                    f"{len(all_cards)}] {toml_id} {card['name']} "
                    f"→ {text_preview}"
                )

        print(f"\n処理完了: 成功 {processed} 件 / 失敗 {failed} 件")

    print("\nTOML ファイルを更新中...")
    cards_by_type: dict[str, list[dict]] = {t: [] for t in TYPE_TO_FILE}

    for toml_id, data in extracted.items():
        card_type = data.get("type", "unknown")
        if card_type not in cards_by_type:
            print(f"  [SKIP] 未対応タイプ {card_type}: {toml_id}")
            continue
        card = build_card_entry(toml_id, data, existing_toml)
        cards_by_type[card_type].append(card)

    write_toml_files(cards_by_type)
    print("\n完了！")
    print(f"中間データ: {EXTRACTED_JSON}")


if __name__ == "__main__":
    main()
