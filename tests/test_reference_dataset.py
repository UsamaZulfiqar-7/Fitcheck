import json

import pytest

from scripts import upload_reference_dataset as uploader


def test_upload_requires_local_minio_configuration(tmp_path, monkeypatch):
    archive = tmp_path / "onet.zip"
    archive.write_bytes(b"archive")
    monkeypatch.setattr(uploader.config, "MINIO_ENDPOINT", "")

    with pytest.raises(RuntimeError, match="MinIO is not configured"):
        uploader.upload_archive(archive)


def test_upload_creates_private_reference_bucket_and_provenance(tmp_path, monkeypatch):
    pytest.importorskip("minio")
    archive = tmp_path / "onet.zip"
    archive.write_bytes(b"archive data")
    calls = []

    class FakeClient:
        def __init__(self, endpoint, access_key, secret_key, secure):
            calls.append(("client", endpoint, access_key, secret_key, secure))

        def bucket_exists(self, bucket):
            calls.append(("bucket_exists", bucket))
            return False

        def make_bucket(self, bucket):
            calls.append(("make_bucket", bucket))

        def put_object(self, bucket, name, data, length, content_type):
            calls.append(("put_object", bucket, name, data.read(), length, content_type))

    monkeypatch.setattr(uploader.config, "MINIO_ENDPOINT", "localhost:9000")
    monkeypatch.setattr(uploader.config, "MINIO_ACCESS_KEY", "test-access")
    monkeypatch.setattr(uploader.config, "MINIO_SECRET_KEY", "test-secret")
    monkeypatch.setattr(uploader.config, "MINIO_BUCKET", "fitcheck-uploads-private")
    monkeypatch.setattr(uploader.config, "MINIO_REFERENCE_BUCKET", "fitcheck-reference-data")
    monkeypatch.setattr(uploader.config, "MINIO_SECURE", False)
    monkeypatch.setattr("minio.Minio", FakeClient)

    archive_object, metadata_object = uploader.upload_archive(archive)

    assert archive_object == "onet/31.0/db_31_0_text.zip"
    assert metadata_object == "onet/31.0/metadata.json"
    uploads = [call for call in calls if call[0] == "put_object"]
    assert [call[1] for call in uploads] == ["fitcheck-reference-data"] * 2
    assert {call[1] for call in calls if call[0] == "make_bucket"} == {
        "fitcheck-reference-data",
        "fitcheck-uploads-private",
    }
    assert uploads[0][3] == b"archive data"
    metadata = json.loads(uploads[1][3])
    assert metadata["version"] == "31.0"
    assert "not a dataset of current job advertisements" in metadata["limitations"]
    assert "license_url" in metadata
