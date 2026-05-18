from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from . import models, schemas
from .database import Base, engine, get_db
from .seed import seed_initial_data

FIXED_USER_ID = 1

app = FastAPI(title="Mobile Order Mock Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"message": "入力値が不正です。"})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else "エラーが発生しました。"
    return JSONResponse(status_code=exc.status_code, content={"message": detail})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"message": "想定外エラーが発生しました。"})


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = next(get_db())
    try:
        seed_initial_data(db)
    finally:
        db.close()


def build_cart_item_response(cart_item: models.CartItem) -> schemas.CartItemResponse:
    return schemas.CartItemResponse(
        id=cart_item.id,
        product=schemas.CartItemProduct(
            id=cart_item.product.id,
            name=cart_item.product.name,
            price=cart_item.product.price,
            image_url=cart_item.product.image_url,
        ),
        quantity=cart_item.quantity,
        subtotal=cart_item.product.price * cart_item.quantity,
    )


@app.get("/products", response_model=list[schemas.ProductResponse])
def get_products(db: Session = Depends(get_db)) -> list[models.Product]:
    return db.query(models.Product).filter(models.Product.is_active.is_(True)).all()


@app.get("/cart-items", response_model=list[schemas.CartItemResponse])
def get_cart_items(db: Session = Depends(get_db)) -> list[schemas.CartItemResponse]:
    cart_items = (
        db.query(models.CartItem)
        .options(joinedload(models.CartItem.product))
        .filter(models.CartItem.user_id == FIXED_USER_ID)
        .all()
    )
    return [build_cart_item_response(item) for item in cart_items]


@app.post("/cart-items", response_model=schemas.CartItemResponse)
def add_cart_item(payload: schemas.CartItemCreate, db: Session = Depends(get_db)) -> schemas.CartItemResponse:
    product = db.query(models.Product).filter(models.Product.id == payload.product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="商品が存在しません。")
    if not product.is_active:
        raise HTTPException(status_code=409, detail="販売停止中の商品は追加できません。")

    cart_item = (
        db.query(models.CartItem)
        .filter(models.CartItem.user_id == FIXED_USER_ID, models.CartItem.product_id == payload.product_id)
        .first()
    )

    if cart_item:
        cart_item.quantity += payload.quantity
    else:
        cart_item = models.CartItem(user_id=FIXED_USER_ID, product_id=payload.product_id, quantity=payload.quantity)
        db.add(cart_item)

    db.commit()
    db.refresh(cart_item)
    db.refresh(cart_item, attribute_names=["product"])
    return build_cart_item_response(cart_item)


@app.patch("/cart-items/{cart_item_id}", response_model=schemas.CartItemResponse)
def update_cart_item(cart_item_id: int, payload: schemas.CartItemUpdate, db: Session = Depends(get_db)) -> schemas.CartItemResponse:
    cart_item = (
        db.query(models.CartItem)
        .options(joinedload(models.CartItem.product))
        .filter(models.CartItem.id == cart_item_id, models.CartItem.user_id == FIXED_USER_ID)
        .first()
    )
    if cart_item is None:
        raise HTTPException(status_code=404, detail="カート商品が存在しません。")

    cart_item.quantity = payload.quantity
    db.commit()
    db.refresh(cart_item)
    return build_cart_item_response(cart_item)


@app.delete("/cart-items/{cart_item_id}", response_model=schemas.MessageResponse)
def delete_cart_item(cart_item_id: int, db: Session = Depends(get_db)) -> schemas.MessageResponse:
    cart_item = (
        db.query(models.CartItem)
        .filter(models.CartItem.id == cart_item_id, models.CartItem.user_id == FIXED_USER_ID)
        .first()
    )
    if cart_item is None:
        raise HTTPException(status_code=404, detail="カート商品が存在しません。")

    db.delete(cart_item)
    db.commit()
    return schemas.MessageResponse(message="カート商品を削除しました。")


@app.post("/orders", response_model=schemas.OrderDetailResponse)
def create_order(db: Session = Depends(get_db)) -> schemas.OrderDetailResponse:
    response_items: list[schemas.OrderItemResponse] = []
    try:
        with db.begin():
            cart_items = (
                db.query(models.CartItem)
                .options(joinedload(models.CartItem.product))
                .filter(models.CartItem.user_id == FIXED_USER_ID)
                .all()
            )
            if not cart_items:
                raise HTTPException(status_code=409, detail="カートが空です。")

            total_amount = sum(item.product.price * item.quantity for item in cart_items)
            order = models.Order(user_id=FIXED_USER_ID, status="ordered", total_amount=total_amount)
            db.add(order)
            db.flush()

            for item in cart_items:
                order_item = models.OrderItem(
                    order_id=order.id,
                    product_id=item.product_id,
                    product_name_at_order=item.product.name,
                    price_at_order=item.product.price,
                    quantity=item.quantity,
                )
                db.add(order_item)
                response_items.append(
                    schemas.OrderItemResponse(
                        product_id=item.product_id,
                        product_name=item.product.name,
                        price=item.product.price,
                        quantity=item.quantity,
                        subtotal=item.product.price * item.quantity,
                    )
                )

            for item in cart_items:
                db.delete(item)

        db.refresh(order)
        return schemas.OrderDetailResponse(
            id=order.id,
            status=order.status,
            total_amount=order.total_amount,
            ordered_at=order.ordered_at,
            items=response_items,
        )
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="注文処理に失敗しました。") from exc


@app.get("/orders", response_model=list[schemas.OrderResponse])
def get_orders(db: Session = Depends(get_db)) -> list[models.Order]:
    return (
        db.query(models.Order)
        .filter(models.Order.user_id == FIXED_USER_ID)
        .order_by(models.Order.ordered_at.desc(), models.Order.id.desc())
        .all()
    )


@app.get("/orders/{order_id}", response_model=schemas.OrderDetailResponse)
def get_order_detail(order_id: int, db: Session = Depends(get_db)) -> schemas.OrderDetailResponse:
    order = (
        db.query(models.Order)
        .options(joinedload(models.Order.items))
        .filter(models.Order.id == order_id, models.Order.user_id == FIXED_USER_ID)
        .first()
    )
    if order is None:
        raise HTTPException(status_code=404, detail="注文が存在しません。")

    items = [
        schemas.OrderItemResponse(
            product_id=item.product_id,
            product_name=item.product_name_at_order,
            price=item.price_at_order,
            quantity=item.quantity,
            subtotal=item.price_at_order * item.quantity,
        )
        for item in order.items
    ]

    return schemas.OrderDetailResponse(
        id=order.id,
        status=order.status,
        total_amount=order.total_amount,
        ordered_at=order.ordered_at,
        items=items,
    )
