import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """プロジェクトルートディレクトリのPathを返す"""
    return Path(__file__).parent.parent


@pytest.fixture
def fixtures_dir():
    """テスト用フィクスチャディレクトリのPathを返す"""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def card_data_dir(project_root):
    """実際のcard_dataディレクトリのPathを返す"""
    return project_root / "card_data"