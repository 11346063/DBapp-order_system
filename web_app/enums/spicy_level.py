from django.db import models


class SpicyLevel(models.IntegerChoices):
    NONE = 0, "不辣"
    MILD = 1, "小辣"
    MEDIUM = 2, "中辣"
    HOT = 3, "大辣"

    @classmethod
    def from_label(cls, label):
        label = (label or "").strip()
        for level in cls:
            if level.label == label:
                return level
        return cls.NONE

    @classmethod
    def display(cls, value):
        try:
            return cls(value).label
        except ValueError:
            return f"辣度{value}"
