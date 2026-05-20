import config


def test_chroma_collection_name_tracks_embedding_model(monkeypatch):
    monkeypatch.setattr(config, "CHROMA_COLLECTION_NAME", None)
    monkeypatch.setattr(config, "EMBEDDING_MODEL", "BAAI/bge-m3")

    assert config.chroma_collection_name().startswith("drive_pipeline_baai_bge-m3_")
    assert len(config.chroma_collection_name()) <= 63


def test_chroma_collection_name_can_be_overridden(monkeypatch):
    monkeypatch.setattr(config, "CHROMA_COLLECTION_NAME", "drive_pipeline")
    monkeypatch.setattr(config, "EMBEDDING_MODEL", "BAAI/bge-m3")

    assert config.chroma_collection_name() == "drive_pipeline"
