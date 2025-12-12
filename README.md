# 1. EXPENSE TRACKER

  A personal expense tracker Flask application

## 3. Description

  Meant for those tired of receit tracking and all the tedious calculations. Expense Tracker helps users view and manage their expenses such as where and how they spend most of their income, set budget limits for certain expenses and/or needs, see how much from the budget limit is already spent, and be able to view the entire data represented by charts.

  In the application users can enter their incheckcome for the current month, this income will be required in the /add-expense page where user(s) can enter necessary information about the expense the user(s) wishes to spend money on (including merchant, amount of expense, currency, etc).

#### 4. Usage

## 4.1. Authentication

  Contains the Login and Registration/Signup routes. Using Werkzeug to secure a user's profile from being accessed by another party. On Signup, the user is checked in the databse if user exists, if not then generate_password_hash is used to secure that user's password by storing it hashed.

  ```py
    from werkzeug.security import check_password_hash, generate_password_hash
  ```

  We also import helpers and models python files where tables are defined.

  Users are stored in the users table using SQLAlchemy ORM Data Model (please check the requirements.txt file for all the dependecies required by this project/app) and passwords are hashed in the Model itself:

  ```py
  class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(250), nullable=False)

    def set_password(self, password):
      self.password_hash = generate_password_hash(password)

    def check_password(self, password):
      return check_password_hash(self.password_hash, password)
  ```

  From helpers.py

  ```py
  # simple login_required decorator using session
  def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
      if session.get("user_id") is None:
        return redirect("/login")
      return f(*args, **kwargs)
    return decorated_function
  ```

## 4.2. Dashboard

  A quick view/access enables users to see their recent expenses, expense that is mostly spent on (ordered by category), and a recent budget entry (the recently set budget limit for a category) provided that a user has any.

## 4.3. Expenses

  Add an expense or more expenses one at a time. View your expenses represented in a table with relevant information including when was the expense created and which to category it belongs.

## 4.4. Budgetting

  Create a budget for a Category (Food, Shopping, Utilities, Electricity, etc.) and set a limit for that budget based on its category. This process involves the budget view table updating dynamically using JavaScript/JQuery DataTables.

  Total spent remains 0 for as long as user has not spent on an expense involving the budget entry category, if user does then toal_spent is subtracted from the budget limit thus remaining amount = budget limit - total spent.

## 4.5. Reports

  All your data from budgetting and expenses is represented in chart to give more of that visual appeal view and clarity on spendings.

## 4.6. Profile

  User enters their income for the current month and the income will be save for use in the budgeting route.

### 4.6.0.1. Installation

  It is highly recommended to use a virtual environment to isolate project dependencies from your system's Python packages. Run these commands accordingly.

  Clone the app/project:

  ```bash
  git clone https://github.com/project-link.git/
  ```

  ```bash
  cd project

  python -m venv venv


  source venv/bin/activate

  ```

  Installing dependecies:

  ```bash
  pip install -r requirements.txt
  ```

  Running the app:

  ```bash
  flask run
  ```

  OR run the app on auto-reload and or in debug mode as well

  ```bash
  flask run --reload
  ```

  Testing and debugging:

  ```bash
  flask run --reload --debug
  ```

  Running effective and fast tests during build:

  ```bash
  flask run --reload --debug
  ```

## 4.7. AUTHOR: ANDRIES N. MOGASHOA
