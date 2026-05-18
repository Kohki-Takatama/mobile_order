from sqlalchemy.orm import Session

from . import models

DEFAULT_USER = {
    "id": 1,
    "name": "Mock User",
    "email": "mock-user@example.com",
}

DEFAULT_PRODUCTS = [
    {"name": "アイスコーヒー", "description": "すっきり飲みやすいアイスコーヒーです。", "price": 350},
    {"name": "ホットコーヒー", "description": "香り豊かな定番ホットコーヒーです。", "price": 300},
    {"name": "カフェラテ", "description": "ミルクたっぷりのやさしい味わいです。", "price": 450},
    {"name": "紅茶", "description": "すっきりとした飲み口の紅茶です。", "price": 320},
    {"name": "サンドイッチ", "description": "野菜とハムを挟んだサンドイッチです。", "price": 600},
    {"name": "チーズケーキ", "description": "濃厚でなめらかなチーズケーキです。", "price": 500},
]


def seed_initial_data(db: Session) -> None:
    user = db.query(models.User).filter(models.User.id == DEFAULT_USER["id"]).first()
    if user is None:
        db.add(models.User(**DEFAULT_USER))

    product_count = db.query(models.Product).count()
    if product_count == 0:
        for product in DEFAULT_PRODUCTS:
            db.add(
                models.Product(
                    name=product["name"],
                    description=product["description"],
                    price=product["price"],
                    image_url="https://placehold.co/300x200",
                    is_active=True,
                )
            )

    db.commit()
