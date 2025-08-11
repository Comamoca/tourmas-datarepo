import pytest
from pathlib import Path
from validators.card_data import (
    validate_toml_file,
    _validate_all_files,
    _find_toml_files,
    CARD_MODELS,
    CostumeCard,
    AccessoryCard,
    SupportCard,
    SpAppealCard,
)


class TestCardModels:
    """Pydanticカードモデルのテスト"""

    def test_costume_card_validation(self):
        """コスチュームカードの正常バリデーション"""
        card_data = {
            "id": "IMT-01-001",
            "name": "テストコスチューム",
            "idol": "天海 春香",
            "rarity": "SSR",
            "text": "テスト用コスチューム",
            "type": "costume",
            "appeal": {
                "vocal": 1000,
                "dance": 800,
                "visual": 900
            },
            "skill": {
                "name": "テストスキル",
                "description": "スキル説明"
            }
        }
        card = CostumeCard.model_validate(card_data)
        assert card.id == "IMT-01-001"
        assert card.type == "costume"
        assert card.appeal.vocal == 1000

    def test_accessory_card_validation(self):
        """アクセサリーカードの正常バリデーション"""
        card_data = {
            "id": "IMT-02-001",
            "name": "テストアクセサリー",
            "idol": "如月 千早",
            "rarity": "SR",
            "text": "テスト用アクセサリー",
            "type": "accessory",
            "body_part": "head"
        }
        card = AccessoryCard.model_validate(card_data)
        assert card.id == "IMT-02-001"
        assert card.body_part == "head"

    def test_support_card_validation(self):
        """サポートカードの正常バリデーション"""
        card_data = {
            "id": "IMT-03-001",
            "name": "テストサポート",
            "idol": "星井 美希",
            "rarity": "R",
            "text": "テスト用サポート",
            "type": "support",
            "support_skill": {
                "live_type": ["rhythm", "create"],
                "description": ["効果1", "効果2"]
            }
        }
        card = SupportCard.model_validate(card_data)
        assert card.id == "IMT-03-001"
        assert "rhythm" in card.support_skill.live_type

    def test_sp_appeal_card_validation(self):
        """SPアピールカードの正常バリデーション"""
        card_data = {
            "id": "IMT-04-001",
            "name": "テストSPアピール",
            "idol": "萩原 雪歩",
            "rarity": "N",
            "text": "テスト用SPアピール",
            "type": "sp_appeal",
            "sp_appeal": {
                "effect": ["効果1", "効果2"]
            }
        }
        card = SpAppealCard.model_validate(card_data)
        assert card.id == "IMT-04-001"
        assert len(card.sp_appeal.effect) == 2

    def test_invalid_card_id_format(self):
        """無効なカードIDフォーマットのテスト"""
        card_data = {
            "id": "INVALID-ID",
            "name": "テストカード",
            "idol": "テスト アイドル",
            "rarity": "SSR",
            "text": "テスト用",
            "type": "costume",
            "appeal": {"vocal": 100, "dance": 100, "visual": 100}
        }
        with pytest.raises(ValueError, match="カードIDはIMT-XX-XXX形式である必要があります"):
            CostumeCard.model_validate(card_data)

    def test_idol_name_validation(self):
        """アイドル名のバリデーション（現在は任意の文字列を許可）"""
        # スペースありの場合
        card_data_with_space = {
            "id": "IMT-01-001",
            "name": "テストカード",
            "idol": "テスト アイドル",
            "rarity": "SSR",
            "text": "テスト用",
            "type": "costume",
            "appeal": {"vocal": 100, "dance": 100, "visual": 100}
        }
        card1 = CostumeCard.model_validate(card_data_with_space)
        assert card1.idol == "テスト アイドル"
        
        # スペースなしの場合（既存データとの互換性のため許可）
        card_data_without_space = {
            "id": "IMT-01-002",
            "name": "テストカード2",
            "idol": "テストアイドル",
            "rarity": "SSR",
            "text": "テスト用",
            "type": "costume",
            "appeal": {"vocal": 100, "dance": 100, "visual": 100}
        }
        card2 = CostumeCard.model_validate(card_data_without_space)
        assert card2.idol == "テストアイドル"


class TestFileValidation:
    """ファイルレベルでのバリデーションテスト"""

    def test_valid_cards_file(self, fixtures_dir):
        """正常なカードファイルのバリデーション"""
        valid_file = fixtures_dir / "valid_cards.toml"
        errors = validate_toml_file(valid_file, verbose=False)
        assert errors == []

    def test_invalid_cards_file(self, fixtures_dir):
        """無効なカードファイルのバリデーション"""
        invalid_file = fixtures_dir / "invalid_cards.toml"
        errors = validate_toml_file(invalid_file, verbose=False)
        
        assert len(errors) > 0
        
        # 具体的なエラーをチェック
        error_messages = " ".join(errors)
        assert "カードIDはIMT-XX-XXX形式である必要があります" in error_messages
        assert "Field required" in error_messages
        assert "Unknown card type 'unknown_type'" in error_messages
        assert "Duplicate card ID 'IMT-02-002'" in error_messages

    def test_nonexistent_file(self):
        """存在しないファイルのテスト"""
        nonexistent = Path("/nonexistent/file.toml")
        errors = validate_toml_file(nonexistent, verbose=False)
        assert len(errors) == 1
        assert "File not found" in errors[0]


class TestBulkValidation:
    """複数ファイル一括バリデーションのテスト"""

    def test_validate_all_files_with_valid_data(self, fixtures_dir, project_root):
        """正常データでの一括バリデーション"""
        toml_files = [fixtures_dir / "valid_cards.toml"]
        errors = _validate_all_files(toml_files, project_root, verbose=False)
        assert errors == []

    def test_validate_all_files_with_invalid_data(self, fixtures_dir, project_root):
        """無効データでの一括バリデーション"""
        toml_files = [fixtures_dir / "invalid_cards.toml"]
        errors = _validate_all_files(toml_files, project_root, verbose=False)
        assert len(errors) > 0

    def test_validate_actual_card_data(self, card_data_dir, project_root):
        """実際のcard_dataディレクトリのバリデーション"""
        try:
            toml_files = _find_toml_files(card_data_dir)
        except FileNotFoundError:
            pytest.skip("card_data directory not found")
        
        if not toml_files:
            pytest.skip("No TOML files found in card_data")
        
        errors = _validate_all_files(toml_files, project_root, verbose=False)
        assert errors == [], f"Validation errors found in actual data: {errors}"


class TestCardTypeMapping:
    """カードタイプマッピングのテスト"""

    def test_card_models_mapping(self):
        """CARD_MODELSマッピングの確認"""
        expected_types = ["costume", "accessory", "support", "sp_appeal"]
        assert set(CARD_MODELS.keys()) == set(expected_types)
        
        assert CARD_MODELS["costume"] == CostumeCard
        assert CARD_MODELS["accessory"] == AccessoryCard
        assert CARD_MODELS["support"] == SupportCard
        assert CARD_MODELS["sp_appeal"] == SpAppealCard


@pytest.mark.parametrize("card_type,required_fields", [
    ("costume", ["appeal"]),
    ("accessory", ["body_part"]),
    ("support", ["support_skill"]),
    ("sp_appeal", ["sp_appeal"]),
])
def test_card_type_specific_fields(card_type, required_fields):
    """各カードタイプの必須フィールドテスト"""
    base_data = {
        "id": "IMT-01-001",
        "name": "テストカード",
        "idol": "テスト アイドル",
        "rarity": "SSR",
        "text": "テスト用",
        "type": card_type
    }
    
    model = CARD_MODELS[card_type]
    
    # 必須フィールドなしではエラーになることを確認
    with pytest.raises(ValueError):
        model.model_validate(base_data)