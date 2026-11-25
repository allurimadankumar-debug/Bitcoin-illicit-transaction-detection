from fastapi import APIRouter, HTTPException

from app.core.config import PUBLIC_CONFIG, get_settings
from app.schemas.settings import SettingsResponse, SettingsUpdateRequest
from app.services.settings_service import all_settings, update_settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
def get_settings_route() -> SettingsResponse:
    overrides = all_settings()
    return SettingsResponse(
        explorer_base_url=overrides["explorer_base_url"],
        enable_live_lookup=bool(overrides["enable_live_lookup"]),
        mask_ids_by_default=bool(overrides["mask_ids_by_default"]),
        dataset_source=get_settings().dataset_source,
        version=PUBLIC_CONFIG["version"],
        keys_required=PUBLIC_CONFIG["keys_required"],
        overrides=overrides,
        note=(
            "Preferences only. Private keys, seed phrases and API secrets are never "
            "requested, stored or returned by this application."
        ),
    )


@router.post("", response_model=SettingsResponse)
def update_settings_route(payload: SettingsUpdateRequest) -> SettingsResponse:
    try:
        update_settings(payload.model_dump(exclude_none=True))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return get_settings_route()
