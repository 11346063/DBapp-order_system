from django.db import transaction

from web_app.constants import (
    EXTRA_INGREDIENT_COST,
    OPTION_BASIL,
    OPTION_CUT,
    OPTION_GARLIC,
    OPTION_SPICY,
)
from web_app.models import Options
from web_app.models.store_settings import StoreSettings

_DEFAULTS = {
    "extra_ingredient_cost": EXTRA_INGREDIENT_COST,
    "option_name_spicy": OPTION_SPICY,
    "option_name_garlic": OPTION_GARLIC,
    "option_name_basil": OPTION_BASIL,
    "option_name_cut": OPTION_CUT,
}

_OPTION_FIELDS = [
    "option_name_spicy",
    "option_name_garlic",
    "option_name_basil",
    "option_name_cut",
]


def get_settings() -> StoreSettings:
    obj, _ = StoreSettings.objects.get_or_create(pk=1, defaults=_DEFAULTS)
    return obj


def update_settings(new_data: dict) -> StoreSettings:
    current = get_settings()

    with transaction.atomic():
        for field in _OPTION_FIELDS:
            old_name = getattr(current, field)
            new_name = new_data.get(field, old_name)
            if new_name and new_name != old_name:
                Options.objects.filter(name=old_name).update(name=new_name)

        StoreSettings.objects.filter(pk=1).update(
            **{
                k: v
                for k, v in new_data.items()
                if k in {"extra_ingredient_cost"} | set(_OPTION_FIELDS)
            }
        )

    return get_settings()
