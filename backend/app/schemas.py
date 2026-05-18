from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    message: str


class ProductResponse(BaseModel):
    id: int
    name: str
    description: str
    price: int
    image_url: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class CartItemProduct(BaseModel):
    id: int
    name: str
    price: int
    image_url: str


class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartItemResponse(BaseModel):
    id: int
    product: CartItemProduct
    quantity: int
    subtotal: int


class MessageResponse(BaseModel):
    message: str


class OrderItemResponse(BaseModel):
    product_id: int
    product_name: str
    price: int
    quantity: int
    subtotal: int


class OrderResponse(BaseModel):
    id: int
    status: str
    total_amount: int
    ordered_at: datetime


class OrderDetailResponse(OrderResponse):
    items: list[OrderItemResponse]
