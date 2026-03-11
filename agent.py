# agent.py
from dataclasses import dataclass
from typing import Any
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider
from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from sqlalchemy.orm import Session
import os

from models import Product, User

load_dotenv()

# --- 1. Structured Output Schema ---
class ProductResponse(BaseModel):
    available: bool
    suggestions: list[str]
    message: str

# --- 2. Agent Dependencies ---
@dataclass
class Deps:
    db: Session
    user_id: Any

# --- 3. The Agent Definition ---
product_agent = Agent[Deps, ProductResponse](
    model=GroqModel(
        'llama-3.3-70b-versatile',
        provider=GroqProvider(api_key=os.getenv("GROQ_API_KEY"))
    ),
    output_type=ProductResponse,
    defer_model_check=True,
    system_prompt="""You are a helpful e-commerce assistant.
    ALWAYS use the get_product_stock tool to check product availability.
    ALWAYS respond with a valid JSON object with exactly these fields:
    - available (bool): whether the product is in stock
    - suggestions (list[str]): related suggestions or empty list
    - message (str): a helpful response to the user
    """
)  # type: ignore[reportCallIssue]

# --- 4. Tool: Read product stock ---
@product_agent.tool
def get_product_stock(ctx: RunContext[Deps], name: str) -> str:
    """Checks the database for a product by name."""
    product = ctx.deps.db.query(Product).filter(Product.name.contains(name)).first()
    if product:
        return f"Found {product.name}: {product.stock} in stock at ${product.price}."
    return "Product not found."

# --- 5. Tool: Update product stock (admin only) ---
@product_agent.tool
def update_product_stock(ctx: RunContext[Deps], product_id: int, new_stock: int) -> str:
    """
    Update the stock level for a specific product.
    ONLY allowed if the requesting user is an admin.
    """
    # FIX: Use ctx.deps.user_id instead of accepting user_id as a parameter —
    # accepting it as a parameter allowed the AI (or a caller) to pass any arbitrary
    # user_id, bypassing the auth check entirely.
    user = ctx.deps.db.query(User).filter(User.id == ctx.deps.user_id).first()

    if not user or not bool(user.is_admin):
        return "Permission Denied: Only admins can update stock."

    product = ctx.deps.db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return "Error: Product not found."

    product.stock = new_stock
    ctx.deps.db.commit()
    return f"Success: {product.name} stock updated to {new_stock}."
