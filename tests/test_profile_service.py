from fat_loss_agent.repositories.db import init_db
from fat_loss_agent.repositories.profile_repo import ProfileRepository
from fat_loss_agent.services.profile_service import ProfileService


def test_profile_service_upserts_and_reads_profile(tmp_path):
    db_path = tmp_path / "app.db"
    init_db(db_path)
    service = ProfileService(ProfileRepository(db_path))

    saved = service.save_profile(
        user_id="local_user",
        nickname="Yao",
        sex="male",
        age=30,
        height_cm=175,
        current_weight_kg=80,
        target_weight_kg=72,
        activity_level="moderate",
        fat_loss_speed="standard",
        diet_preferences="少油",
    )

    loaded = service.get_profile("local_user")
    assert loaded is not None
    assert loaded["nickname"] == "Yao"
    assert saved["daily_protein_target_g"] == 128
