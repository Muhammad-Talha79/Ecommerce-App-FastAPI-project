"""
CRUD functions interacting with the database.
"""

from sqlalchemy.orm import Session
import models, schemas
from hashing import hash_password, verify_password


# ========================================================
# USER CRUD
# ========================================================

def create_user(db: Session, user: schemas.UserCreate):
    hashed_pw = hash_password(user.password)
    # FIX: 'name' field was never being saved — added name=user.name
    db_user = models.User(name=user.name, email=user.email, hashed_password=hashed_pw)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def authenticate_user(db: Session, email: str, password: str):
    """
    Authenticate user credentials.
    """
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# ========================================================
# PRODUCT CRUD
# ========================================================

def create_product(db: Session, product: schemas.ProductCreate):
    """
    Insert a new product into the database.
    """
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def get_products(db: Session):
    """
    Retrieve all products.
    """
    return db.query(models.Product).all()

def get_product(db: Session, product_id: int):
    """
    Retrieve a single product by ID.
    """
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def update_product(db: Session, product_id: int, product: schemas.ProductCreate):
    """
    Update product details.
    """
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        return None
    for key, value in product.model_dump().items():
        setattr(db_product, key, value)
    db.commit()
    db.refresh(db_product)
    return db_product

def delete_product(db: Session, product_id: int):
    """
    Remove a product from the database.
    """
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        return None
    db.delete(db_product)
    db.commit()
    return db_product
