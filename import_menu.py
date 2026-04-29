"""
匯入 CSV 菜單資料到資料庫
用法: python manage.py shell < import_menu.py
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "order_system.settings")
django.setup()

from web_app.models import Menu, Type  # noqa: E402

# 定義分類規則
CATEGORY_RULES = {
    "碳烤區": ["碳烤香雞排", "烤雞胗", "烤雞心", "烤雞翅", "烤米血"],
    "蔬菜區": [
        "玉米",
        "青椒",
        "四季豆",
        "玉米筍",
        "小黃瓜",
        "青花椰",
        "炸香菇",
        "高麗菜",
        "杏鮑菇",
        "洋蔥",
    ],
}


def get_category(item_name):
    for cat, items in CATEGORY_RULES.items():
        if item_name in items:
            return cat
    return "炸物區"


# CSV 資料
menu_items = [
    ("碳烤香雞排", 75),
    ("烤雞胗", 25),
    ("烤雞心", 25),
    ("烤雞翅", 25),
    ("烤米血", 20),
    ("炸雞排", 70),
    ("魷魚絲", 50),
    ("魷魚圈", 50),
    ("軟骨", 50),
    ("三角骨", 50),
    ("雞背", 50),
    ("鹽酥雞", 50),
    ("脆薯條", 30),
    ("花枝丸", 30),
    ("貢丸", 30),
    ("波浪薯條", 30),
    ("地瓜條", 30),
    ("山藥捲*2", 30),
    ("甜不辣", 30),
    ("雞皮", 25),
    ("雞屁股", 25),
    ("雞肉香腸", 25),
    ("大熱狗", 25),
    ("米腸", 25),
    ("大甜片", 20),
    ("百頁豆腐", 20),
    ("鱈魚丸", 20),
    ("芋頭餅", 20),
    ("魚板", 20),
    ("炸皮蛋", 20),
    ("銀絲卷", 20),
    ("四角薯餅", 20),
    ("芋包", 20),
    ("芋粿", 20),
    ("豆包", 15),
    ("黑輪", 10),
    ("蘿蔔糕", 10),
    ("小熱狗*2", 10),
    ("豆干*2", 10),
    ("水餃*7", 30),
    ("玉米可樂餅*3", 30),
    ("洋蔥圈*3", 30),
    ("柳葉魚", 15),
    ("玉米", 40),
    ("青椒", 30),
    ("四季豆", 30),
    ("玉米筍", 30),
    ("小黃瓜", 30),
    ("青花椰", 25),
    ("炸香菇", 25),
    ("高麗菜", 25),
    ("杏鮑菇", 25),
    ("洋蔥", 20),
]

# 建立分類
categories = set(get_category(name) for name, _ in menu_items)
type_map = {}
for cat_name in categories:
    type_obj, created = Type.objects.get_or_create(type_name=cat_name)
    type_map[cat_name] = type_obj
    status = "新建" if created else "已存在"
    print(f"  分類 [{cat_name}] {status}")

print(f"\n共 {len(categories)} 個分類")
print("-" * 40)

# 匯入餐點
created_count = 0
skipped_count = 0

for name, price in menu_items:
    category = get_category(name)
    type_obj = type_map[category]

    menu, created = Menu.objects.get_or_create(
        name=name,
        defaults={
            "type": type_obj,
            "price": price,
        },
    )

    if created:
        created_count += 1
        print(f"  + [{category}] {name} ${price}")
    else:
        skipped_count += 1
        print(f"  - [{category}] {name} 已存在，跳過")

print("-" * 40)
print(f"匯入完成！新增 {created_count} 筆，跳過 {skipped_count} 筆")
print(f"資料庫目前共有 {Menu.objects.count()} 個餐點")
