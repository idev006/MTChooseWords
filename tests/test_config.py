from app.core.config import AppConfig
from app.core.paths import PathManager
from app.core.source_adapters import default_source_registry


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


def test_committed_config_points_to_production_docx_txt_sources():
    config = AppConfig.load(AppConfig().resolve("config.toml"))
    sources = [config.resolve(value) for value in config.word_source_files]

    assert sources
    assert all(source.exists() for source in sources)
    assert not any(source.suffix.lower() == ".pdf" for source in sources)
    assert {path.suffix.lower() for path in default_source_registry().sources_from(sources)} == {".docx", ".txt"}
    assert config.database == "app/mtchoosewords.sqlite3"
    assert config.clear_words_before_import is True


def test_path_manager_keeps_project_paths_relative(tmp_path):
    paths = PathManager(tmp_path)
    source = tmp_path / "app/assets/words/text/คลังคำศัพท์ภาษาไทย_ป1_VISUAL_VERIFIED.txt"
    external = tmp_path.parent / "outside.txt"

    assert paths.resolve("app/assets/fonts") == tmp_path / "app/assets/fonts"
    assert paths.to_config_value(source) == "app/assets/words/text/คลังคำศัพท์ภาษาไทย_ป1_VISUAL_VERIFIED.txt"
    assert paths.to_config_value(external) == str(external)
