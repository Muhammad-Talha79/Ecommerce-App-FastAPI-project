from typing import Optional

from pydantic import BaseModel, EmailStr

# ========================================================
# USER SCHEMAS
# ========================================================

class UserBase(BaseModel):
    name: Optional[str]
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    is_admin: bool

    class Config:
        from_attributes = True


# ========================================================
# PRODUCT SCHEMAS
# ========================================================

class ProductBase(BaseModel):
    name: str
    description: str
    price: float
    stock: int


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int

    class Config:
        from_attributes = True


# ========================================================
# ORDER SCHEMAS
# ========================================================

class OrderBase(BaseModel):
    product_id: int
    quantity: int


class OrderCreate(OrderBase):
    user_id: int


class OrderResponse(OrderBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True