from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)

    hashed_password: Mapped[str] = mapped_column(String)

    is_admin = Column(Boolean, default=False)

    # relationship
    orders = relationship("Order", back_populates="user")


class Product(Base):
    __tablename__ = "products"

    id : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name : Mapped[str] = mapped_column(String, index=True)
    description : Mapped[str] = mapped_column(String)
    price : Mapped[float] = mapped_column(Float)
    stock : Mapped[int] = mapped_column(Integer)

    orders = relationship("Order", back_populates="product")


class Order(Base):
    __tablename__ = "orders"

    id : Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id : Mapped[int] = mapped_column   (Integer, ForeignKey("users.id"))
    product_id : Mapped[int] = mapped_column(Integer, ForeignKey("products.id"))

    quantity : Mapped[int] = mapped_column(Integer)

    user = relationship("User", back_populates="orders")
    product = relationship("Product", back_populates="orders")
