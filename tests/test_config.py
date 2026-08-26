from app.core.config import AppConfig


def test_config_round_trip(tmp_path):
    path = tmp_path / "config.toml"
    original = AppConfig(title="ทดสอบ", pages=3, words_per_page=12, document_sets=4, title_margin_bottom_px=25, title_padding_px=8, title_bgcolor="#EEEEEE", colors=["#123456"])
    original.save(path)
    loaded = AppConfig.load(path)
    assert loaded.title == original.title
    assert loaded.pages == 3
    assert loaded.words_per_page == 12
    assert loaded.document_sets == 4
    assert loaded.title_margin_bottom_px == 25
    assert loaded.title_padding_px == 8
    assert loaded.title_bgcolor == "#EEEEEE"
    assert loaded.colors == ["#123456"]
