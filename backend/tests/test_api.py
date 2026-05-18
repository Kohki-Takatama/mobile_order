from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app
from app.seed import seed_initial_data


@pytest.fixture()
def client(tmp_path: pytest.TempPathFactory) -> Generator[TestClient, None, None]:
    db_file = tmp_path / "test_mobile_order.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)
    db: Session = TestingSessionLocal()
    seed_initial_data(db)
    db.close()

    def override_get_db() -> Generator[Session, None, None]:
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_get_products(client: TestClient) -> None:
    response = client.get("/products")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 6
    assert all(item["is_active"] is True for item in data)


def test_cart_add_get_patch_delete_flow(client: TestClient) -> None:
    add_response = client.post("/cart-items", json={"product_id": 1, "quantity": 1})
    assert add_response.status_code == 200
    add_data = add_response.json()
    assert add_data["quantity"] == 1

    # 同じ商品を追加すると数量加算
    add_again = client.post("/cart-items", json={"product_id": 1, "quantity": 2})
    assert add_again.status_code == 200
    assert add_again.json()["quantity"] == 3

    list_response = client.get("/cart-items")
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert len(list_data) == 1
    cart_item_id = list_data[0]["id"]

    patch_response = client.patch(f"/cart-items/{cart_item_id}", json={"quantity": 5})
    assert patch_response.status_code == 200
    assert patch_response.json()["quantity"] == 5

    delete_response = client.delete(f"/cart-items/{cart_item_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "カート商品を削除しました。"

    list_after_delete = client.get("/cart-items")
    assert list_after_delete.status_code == 200
    assert list_after_delete.json() == []


def test_cart_error_cases(client: TestClient) -> None:
    not_found_product = client.post("/cart-items", json={"product_id": 9999, "quantity": 1})
    assert not_found_product.status_code == 404

    invalid_quantity = client.post("/cart-items", json={"product_id": 1, "quantity": 0})
    assert invalid_quantity.status_code == 400

    missing_cart_item = client.patch("/cart-items/9999", json={"quantity": 2})
    assert missing_cart_item.status_code == 404

    missing_cart_item_delete = client.delete("/cart-items/9999")
    assert missing_cart_item_delete.status_code == 404


def test_order_create_history_detail_flow(client: TestClient) -> None:
    # カートに商品追加
    client.post("/cart-items", json={"product_id": 1, "quantity": 2})
    client.post("/cart-items", json={"product_id": 2, "quantity": 1})

    order_response = client.post("/orders")
    assert order_response.status_code == 200
    order_data = order_response.json()
    assert order_data["status"] == "ordered"
    assert len(order_data["items"]) == 2

    # 注文後はカートが空
    cart_response = client.get("/cart-items")
    assert cart_response.status_code == 200
    assert cart_response.json() == []

    history_response = client.get("/orders")
    assert history_response.status_code == 200
    history_data = history_response.json()
    assert len(history_data) == 1

    order_id = history_data[0]["id"]
    detail_response = client.get(f"/orders/{order_id}")
    assert detail_response.status_code == 200
    detail_data = detail_response.json()
    assert detail_data["id"] == order_id
    assert len(detail_data["items"]) == 2


def test_order_error_cases(client: TestClient) -> None:
    empty_cart_order = client.post("/orders")
    assert empty_cart_order.status_code == 409

    missing_order = client.get("/orders/9999")
    assert missing_order.status_code == 404
