# main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from database import get_db, engine, Base
from agent import product_agent, Deps, ProductResponse
import models, schemas, crud, auth

# ----------------------------
# Database setup
# ----------------------------
Base.metadata.create_all(bind=engine)

# FIX: Removed global oauth2_scheme dependency — it broke public endpoints
# like /users/register, /token, GET /products, GET /products/{id}
app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ----------------------------
# USER ENDPOINTS
# ----------------------------

@app.post("/users/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = crud.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db, user)

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# FIX: Replaced raw Header(...) approach with the standard OAuth2 get_current_user
# from auth.py — this correctly reads the Bearer token via OAuth2PasswordBearer
def get_current_user(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

def get_current_admin_user(current_user: models.User = Depends(get_current_user)):
    if not bool(current_user.is_admin):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

@app.get("/profile", response_model=schemas.UserResponse)
def profile(current_user: models.User = Depends(get_current_user)):
    return current_user

# ----------------------------
# Agent Endpoint
# ----------------------------

@app.post("/chat", response_model=ProductResponse)
async def chat_with_agent(
    prompt: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    deps = Deps(db=db, user_id=current_user.id)
    # FIX: AgentRunResult.data holds the validated ProductResponse — not the result itself
    result = await product_agent.run(prompt, deps=deps)
    return result.output

# ----------------------------
# PRODUCT ENDPOINTS
# ----------------------------

@app.post("/products", response_model=schemas.ProductResponse)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user)
):
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
def update_product(
    product_id: int,
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user)
):
    updated = crud.update_product(db, product_id, product)
    if not updated:
        raise HTTPException(status_code=404, detail="Product not found")
    return updated

@app.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin_user: models.User = Depends(get_current_admin_user)
):
    deleted_product = crud.delete_product(db, product_id)
    if not deleted_product:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}

# ----------------------------
# ORDER ENDPOINTS
# ----------------------------

@app.post("/orders", response_model=schemas.OrderResponse)
def create_order(
    order: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot create order for another user")

    # FIX: Check product exists and has sufficient stock before placing order
    product = crud.get_product(db, order.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock < order.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    db_order = models.Order(
        user_id=order.user_id,
        product_id=order.product_id,
        quantity=order.quantity
    )
    db.add(db_order)

    # Decrement stock after order
    product.stock -= order.quantity

    db.commit()
    db.refresh(db_order)
    return db_order

@app.get("/orders", response_model=List[schemas.OrderResponse])
def read_orders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if bool(current_user.is_admin):
        return db.query(models.Order).all()
    return db.query(models.Order).filter(models.Order.user_id == current_user.id).all()
