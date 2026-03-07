# main.py
from fastapi import FastAPI, Depends, HTTPException, Header, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List

import models, schemas, crud, auth
from database import get_db, engine, Base

# ----------------------------
# Database setup
# ----------------------------
Base.metadata.create_all(bind=engine)

app = FastAPI(title="E-Commerce API")

# ----------------------------
# USER ENDPOINTS
# ----------------------------

@app.post("/users/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db, user)

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

def get_current_user(authorization: str = Header(...), db: Session = Depends(get_db)) -> models.User:
    token = authorization.split(" ")[1]  # Bearer <token>
    payload = auth.verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_email = payload.get("sub")
    if not user_email:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = crud.get_user_by_email(db, user_email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def get_current_admin_user(current_user: models.User = Depends(get_current_user)):
    if not bool(current_user.is_admin):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

@app.get("/profile", response_model=schemas.UserResponse)
def profile(current_user: models.User = Depends(get_current_user)):
    return current_user

# ----------------------------
# PRODUCT ENDPOINTS
# ----------------------------

@app.post("/products", response_model=schemas.ProductResponse)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db),
                   admin_user: models.User = Depends(get_current_admin_user)):
    return crud.create_product(db, product)

@app.get("/products", response_model=List[schemas.ProductResponse])
def read_products(db: Session = Depends(get_db)):
    return crud.get_products(db)

@app.get("/products/{product_id}", response_model=schemas.ProductResponse)
def read_product(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.put("/products/{product_id}", response_model=schemas.ProductResponse)
def update_product(product_id: int, product: schemas.ProductCreate, db: Session = Depends(get_db),
                   admin_user: models.User = Depends(get_current_admin_user)):
    db_product = crud.get_product(db, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Assign values safely
    db_product.name = product.name
    db_product.description = product.description
    db_product.price = product.price
    db_product.stock = product.stock

    db.commit()
    db.refresh(db_product)
    return db_product

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db),
                   admin_user: models.User = Depends(get_current_admin_user)):
    deleted_product = crud.delete_product(db, product_id)
    if not deleted_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}

# ----------------------------
# ORDER ENDPOINTS
# ----------------------------

@app.post("/orders", response_model=schemas.OrderResponse)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db),
                 current_user: models.User = Depends(get_current_user)):
    # Only allow ordering for logged-in user
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot create order for another user")
    db_order = models.Order(
        user_id=order.user_id,
        product_id=order.product_id,
        quantity=order.quantity
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

@app.get("/orders", response_model=List[schemas.OrderResponse])
def read_orders(db: Session = Depends(get_db),
                current_user: models.User = Depends(get_current_user)):
    # Regular users see only their orders; admins see all
    if bool(current_user.is_admin):
        return db.query(models.Order).all()
    return db.query(models.Order).filter(models.Order.user_id == current_user.id).all()