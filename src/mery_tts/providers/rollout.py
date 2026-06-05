def provider_rollout_status() -> dict[str, str]:
    return {
        "kokoro": "platform-integrated",
        "piper-plus": "platform-integrated",
        "supertonic": "planned",
        "voxcpm2": "planned",
    }


__all__ = ["provider_rollout_status"]
