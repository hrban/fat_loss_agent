import pytest

from fat_loss_agent.services.photo_service import PhotoService, UnsupportedPhotoTypeError


def test_save_upload_stores_image_with_safe_name(tmp_path):
    service = PhotoService(tmp_path / "photos")

    saved_path = service.save_upload(
        user_id="local_user",
        original_filename="午饭.JPG",
        content=b"fake-image-bytes",
    )

    assert saved_path.exists()
    assert saved_path.suffix == ".jpg"
    assert saved_path.parent == tmp_path / "photos"
    assert saved_path.read_bytes() == b"fake-image-bytes"
    assert "local_user" in saved_path.name


def test_save_upload_rejects_unsupported_photo_type(tmp_path):
    service = PhotoService(tmp_path / "photos")

    with pytest.raises(UnsupportedPhotoTypeError):
        service.save_upload(user_id="local_user", original_filename="meal.txt", content=b"not-image")
