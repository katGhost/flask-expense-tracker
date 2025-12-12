from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Float, ForeignKey, Date, select
from werkzeug.security import check_password_hash, generate_password_hash

class Base(DeclarativeBase):
  pass

db = SQLAlchemy()

"""
  Create SQLAlchemy models matching the sql tables in my database.sql file
  ========== Adapted from SQLAlchemy Documentation ==============
  https://docs.sqlalchemy.org/en/20/orm/quickstart.html
"""
# User class model
class User(db.Model):
  __tablename__ = "users"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  email: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
  password_hash: Mapped[str] = mapped_column(String(250), nullable=False)

  # Below In-Model hasshing adapted from ->
  # https://dev.to/goke/securing-your-flask-application-hashing-passwords-tutorial-2f0p
  def set_password(self, password):
    self.password_hash = generate_password_hash(password)
  
  def check_password(self, password):
    return check_password_hash(self.password_hash, password)  

  # Relationships
  income = relationship("Income", back_populates="user", uselist=False)
  categories = relationship("Category", back_populates="user")


# Income model
class Income(db.Model):
  __tablename__ = "incomes"

  id: Mapped[int] = mapped_column(primary_key=True)
  income_value: Mapped[float] = mapped_column(Float, nullable=False)

  # Foreign data
  user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
  user = relationship("User", back_populates="income")

  # A user's income is connected to all their budget entries
  budget_entries = relationship("BudgetEntry", back_populates="income")


# Category model
class Category(db.Model):
  __tablename__ = "categories"

  id: Mapped[int] = mapped_column(Integer, primary_key=True)
  name: Mapped[str] = mapped_column(String(125), nullable=False)

  # Foreign data
  user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
  user = relationship("User", back_populates="categories")

  # Relationships
  budget_entries = relationship("BudgetEntry", back_populates="category")
  expenses = relationship("Expense", back_populates="category")


# Budget entry model
class BudgetEntry(db.Model):
  __tablename__ = "budget_entries"

  id: Mapped[int] = mapped_column(primary_key=True)

  # Foreign data
  category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
  income_id: Mapped[int] = mapped_column(ForeignKey("incomes.id"))

  month: Mapped[int] = mapped_column(Integer, nullable=False)  # Jan to Dec in (1-12)
  year: Mapped[int] = mapped_column(Integer, nullable=False)

  budget_limit: Mapped[float] = mapped_column(Float, nullable=False)

  # Relationships
  category = relationship("Category", back_populates="budget_entries")
  income = relationship("Income", back_populates="budget_entries")

  # Sum expenses automatically -> for now
  expenses = relationship("Expense", back_populates="budget_entry")

# Expenses class model
class Expense(db.Model):
  __tablename__ = "expenses"
    
  id: Mapped[int] = mapped_column(primary_key=True)
  expense: Mapped[str] = mapped_column(String(125), nullable=False)
  merchant: Mapped[str] = mapped_column(String(125), nullable=False)
  amount: Mapped[float] = mapped_column(Float, nullable=False)
  currency: Mapped[str] = mapped_column(String(25), nullable=False)
  created_at: Mapped[str] = mapped_column(String(60))

  # Foreign data
  category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
  budget_entry_id: Mapped[int] = mapped_column(ForeignKey("budget_entries.id"), nullable=True)

  # Relationships
  category = relationship("Category", back_populates="expenses")
  budget_entry = relationship("BudgetEntry", back_populates="expenses")