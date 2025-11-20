"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

# Core app schemas for the New Mum Companion app

class Motherprofile(BaseModel):
    """
    Stores a mum's basic profile and pregnancy dates
    Collection name: "motherprofile"
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email (used to look up profile)")
    last_period_date: Optional[date] = Field(
        None, description="First day of last menstrual period (LMP)"
    )
    due_date: Optional[date] = Field(None, description="Estimated due date (EDD)")

class Note(BaseModel):
    """
    Quick personal notes or symptoms logs for each week
    Collection name: "note"
    """
    email: str = Field(..., description="Email to link notes to a profile")
    week: int = Field(..., ge=1, le=42, description="Gestational week number")
    text: str = Field(..., description="Note text")

# Example schemas (kept for reference; not used by this app directly)
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
