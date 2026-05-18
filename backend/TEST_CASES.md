# APIテストケース一覧（インターン向け）

このドキュメントは、`backend/tests/test_api.py` が何を検証しているかを
学習者向けに読みやすくまとめたものです。

## 1. 商品一覧

### TC-001 商品一覧取得（正常）
- **API**: `GET /products`
- **期待値**:
  - ステータスコード `200`
  - 6件の初期商品が返る
  - すべて `is_active = true`

---

## 2. カート操作

### TC-002 カート追加→取得→数量変更→削除（正常フロー）
- **API**:
  1. `POST /cart-items`（追加）
  2. `POST /cart-items`（同一商品を再追加）
  3. `GET /cart-items`（一覧確認）
  4. `PATCH /cart-items/{cart_item_id}`（数量変更）
  5. `DELETE /cart-items/{cart_item_id}`（削除）
  6. `GET /cart-items`（空確認）
- **期待値**:
  - 同一商品の再追加時に数量が加算される
  - 変更後数量が反映される
  - 削除後にカートが空になる

### TC-003 カート系エラー（異常系）
- **API / 条件**:
  - `POST /cart-items` で存在しない `product_id`
  - `POST /cart-items` で `quantity=0`
  - `PATCH /cart-items/{id}` で存在しないID
  - `DELETE /cart-items/{id}` で存在しないID
- **期待値**:
  - 404（商品なし / カート項目なし）
  - 400（入力値不正）

---

## 3. 注文操作

### TC-004 注文作成→履歴→詳細（正常フロー）
- **API**:
  1. `POST /cart-items`（複数商品を追加）
  2. `POST /orders`（注文作成）
  3. `GET /cart-items`（空確認）
  4. `GET /orders`（履歴確認）
  5. `GET /orders/{order_id}`（詳細確認）
- **期待値**:
  - 注文が `ordered` で作成される
  - 注文後にカートが空になる
  - 履歴・詳細で注文内容が参照できる

### TC-005 注文系エラー（異常系）
- **API / 条件**:
  - 空カートで `POST /orders`
  - 存在しない `order_id` で `GET /orders/{order_id}`
- **期待値**:
  - 409（空カート）
  - 404（注文なし）

---

## 対応する自動テスト関数

- `test_get_products`
- `test_cart_add_get_patch_delete_flow`
- `test_cart_error_cases`
- `test_order_create_history_detail_flow`
- `test_order_error_cases`

実装は `backend/tests/test_api.py` を参照してください。
