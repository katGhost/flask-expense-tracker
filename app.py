import os
from datetime import datetime
from sqlalchemy import select
from flask import Flask, flash, render_template, redirect, request, session, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session

# custom reusable model component
from models import User, Income, Category, Expense, BudgetEntry, db
from helpers import login_required


# configure FLask application
app = Flask(__name__)

# Configure db location/path
basedir = os.path.abspath(os.path.dirname(__file__))

# https://www.reddit.com/r/flask/comments/gvekun/what_are_the_exact_uses_of_flasks_secret_key/
# Reddit on understanding secret_keys
app.secret_key = "your_secret_key"
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = "filesystem"
Session(app)

# Configure SQLAlchemy database
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + os.path.join(basedir, "expenses.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Define base class
# Configure caching
@app.after_request
def after_request(response):
  response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
  response.headers["Expires"] = 0
  response.headers["Pragma"] = "no-cache"
  return response


# Initialize the database tables
db.init_app(app)
with app.app_context():
  db.create_all()
# Fake login for dev purposes
#@app.before_request
#def fake_login():
# session["user_id"] = 1
#------------------------



# Dashboard/Home route
# Views the Overall expense tracking, spending,
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
  # Get user id
  user_id = session.get("user_id") 

  # Get recent expense
  recent_expense = (
    db.session.query(Expense)
    .join(Category)
    .filter(Category.user_id == user_id)
    .order_by(Expense.created_at.desc())
    .first()
  )


  # Get recent budget entry
  recent_budget = (
    db.session.query(BudgetEntry)
    .join(Category)
    .filter(Category.user_id == user_id)
    .order_by(BudgetEntry.id.desc())
    .first()
  )


  # Query category which most money is spent on
  top_category = (
    db.session.query(
      Category.name,
      db.func.sum(Expense.amount).label("total_spent")
    )
    .join(Expense)
    .filter(Category.user_id == user_id)
    .group_by(Category.id)
    .order_by(db.desc("total_spent"))
    .first()
  )

  
  # For now jsut display a Hello Fitness
  theme = session.get("theme", "light")
  
  if request.method == "POST":
    return redirect("/")
  else:
    # Query charts and render charts --> Entire Overall user expense 
    return render_template("index.html", theme=theme, expense=recent_expense, budget=recent_budget, top_category=top_category)

@app.route("/api/chart-data")
@login_required
def bar_chart_endpoint():
  # Get user id
  user_id = session.get("user_id")
  # Adding a bar-chart from the chatJS lib
  # pie-chart for expenses -> Called in Index route
  # Aggregate expenses per category (include categories with zero expenses)
   # Get user id
  user_id = session.get("user_id")
  line_data = (
    db.session.query(
      Category.name,
      db.func.coalesce(db.func.sum(Expense.amount), 0).label("total_spent")
    )
    .outerjoin(Expense, Expense.category_id==Category.id)
    .filter(Category.user_id==user_id)
    .group_by(Category.id, Category.name)
    .order_by(db.func.sum(Expense.amount).desc())
    .all()
  ) # Original adjusted by Copilot

  # Chart.js expects labels and a dataset array
  labels = [row[0] for row in line_data]
  values = [float(row[1]) for row in line_data]

  return jsonify({
    "keys": labels,              
    "values": values,
    "label": "Total Expenses",
    "title": "Expenses by Category" 
    }), 200
  


# Add expense route
@app.route("/add", methods=["GET", "POST"])
@login_required
def add_expense():
  user_id = session.get("user_id")
  if not user_id:
    #flash("You must be logged in")
    return redirect("/login")

  # ----------------------------
  # Ensure categories exist by seeding default categories only once
  existing_names = {c.name for c in Category.query.filter_by(user_id=user_id).all()}
  default_categories = ["Food", "Transport", "Entertainment", "Utilities", "Shopping"]
  

  for name in default_categories:
    if name not in existing_names:
      add_category = Category()
      add_category.name=name
      add_category.user_id=user_id
      db.session.add(add_category)
  db.session.commit()

  # Reload categories after seeding
  categories = Category.query.filter_by(user_id=user_id).all()
    # Get inputs/form
    # Select: category of expenses then: submit
  if request.method == "POST":
    income = request.form.get("income", type=float)
    expense = request.form.get("expense")
    merchant = request.form.get("merchant")
    category_name = request.form.get("category")
    amount = request.form.get("amount", type=float)   # amount spent on the expense
    currency = request.form.get("currency")
    created_at = datetime.now().strftime("%Y-%m-%d")

    # define a new errors list to handle all input errors altogether
    errors = []

    # validate inputs
    if not income:
      errors.append("Income is required")
    if not expense:
      errors.append("Expense is required")
    if not merchant:
      errors.append("Merchant is required")
    if not category_name:
      errors.append("Category is required")
    if not amount:
      errors.append("Amount is required")
    if not currency:
      errors.append("Currency is required")
    
    if errors:
      for err in errors:
        flash(err)
      return redirect("/add")

    # Convert income and amount to itnegerse
    if income is None:
      flash("Income is required")
      return redirect("/add")
    if amount is None:
      flash("Amount is required")
      return redirect("/add")
    
    if amount <= 0 or income <=0:
      flash("Amount must be greater than 0")
      return redirect("/add")

    #--------------------------------------------------
    # Get Category object 
    category_obj = Category.query.filter_by(user_id=user_id, name=category_name).first()

    # Get user income
    user_income = db.session.query(Income).filter(user_id==user_id).first()
    if not user_income:
      return redirect("/profile")
    
    # for current session if amount of expense > income -> do not add expense
    if amount > user_income.income_value:
      flash(f"You cannot afford this expense: {expense}")
  
    # making sure variable types are not None before assigning
    # store income for currently logged-in user and remember user income on next session
    # Insert data into db
    if expense != None and merchant != None and currency != None and amount is not None and created_at != None:
      new_expense = Expense()
      new_expense.expense=expense
      new_expense.merchant=merchant
      new_expense.category=category_obj
      new_expense.amount=amount
      new_expense.currency=currency
      new_expense.created_at=created_at
      
      # use button actions add data to the database
      db.session.add(new_expense)
      db.session.commit()
      flash("Expense added successfully!")
    return redirect("/add")
  return render_template("expense_form.html",mode="add", expense=None, categories=categories)


# Bugeting route and data endpoint
@app.route("/api/add_budget", methods=["GET", "POST"])
def create_budget():
  user_id = session.get("user_id")

  if request.method == "POST":

    data = request.get_json()

    name = data.get("category")
    budget_limit = data.get("budget_limit")
    month = data.get("month")
    year = data.get("year")

    if not user_id:
      return jsonify({"error": "Unauthorized"}), 401
  
    # Validate required fields
    if not all([name, month, year, budget_limit]):
      return jsonify({"success": False, "message": "All fields are required"}), 400

    # Retrieve user's income record
    income = db.session.query(Income).filter_by(user_id=user_id).first()
    if not income:
      return jsonify({"success": False, "message": "All fields are required"}), 400

    # Ensure category exists (create if new)
    category_obj = Category.query.filter_by(user_id=user_id, name=name).first()

    if not category_obj:
      category_obj = Category()
      category_obj.user_id=user_id
      category_obj.name=name
      db.session.add(category_obj)
      db.session.flush()  # Get ID without committing

    # Create budget entry
    new_budget = BudgetEntry()
    new_budget.category_id=category_obj.id
    new_budget.category=category_obj
    new_budget.income_id=income.id
    new_budget.month=month
    new_budget.year=year
    new_budget.budget_limit=budget_limit

    total_spent = db.session.query(
      db.func.sum(Expense.amount)  # since Expense table is linked to BudgetEntry
    ).filter(Expense.budget_entry_id==new_budget.id).scalar() or 0

    db.session.add(new_budget)
    db.session.commit()

    return jsonify({
      "success": True,
      "data": {
        "id": new_budget.id,
        "name": category_obj.name,
        "month": new_budget.month,
        "year": new_budget.year,
        "budget_limit": new_budget.budget_limit,
        "total_spent": total_spent,
        "remaining": new_budget.budget_limit - total_spent
      }
    }), 201
  else:
    # GET method logic, gets the already saved data from the db (if any)
    budgets = (
      db.session.query(BudgetEntry, Category)
      .join(Category, BudgetEntry.category_id==Category.id)
      .filter(Category.user_id==user_id)
      .all()
    )

    # add total spent dynamically
    data = []

    for budget, category in budgets:
      total_spent = db.session.query(
        db.func.sum(Expense.amount)
      ).filter(Expense.category_id==category.id).scalar() or 0
      
      data.append({
        "id": budget.id,
        "name": category.name,
        "month": budget.month,
        "year": budget.year,
        "budget_limit": budget.budget_limit,
        "total_spent": total_spent,
        "remaining": budget.budget_limit - total_spent
      })
      
    return jsonify({"data": data}), 200

# User can set budgets for categories and track their spending habits
# against those limits
@app.route("/budgeting", methods=["GET", "POST"])
@login_required
def budgeting():
  return render_template("budgeting.html")

# Expenses route
# User can view they already have and add a new expense if they want to
# can only view expenses if expenses exist, otherwise nothing
@app.route("/expenses", methods=["GET"])
@login_required
def expenses():
  user_id = session.get("user_id")
  if request.method == "POST":
    return redirect("/expenses")
  
  # Query the expenses database
  res = (
    select(Expense)
    .join(Category)
    .where(Category.user_id == user_id)
    .order_by(Expense.created_at.desc())
  )

  expenses = db.session.execute(res).scalars().all()
  return render_template("expenses.html", expenses=expenses)

  """res = select(Expense).order_by(Expense.created_at)
  expenses = [expense for expense, in db.session.execute(res)]
  return render_template("expenses.html", expenses=expenses)"""

"""
  Some API endpoints to display the REPORTS data represented in charts
"""

@app.route("/api/reports-data")
@login_required
def reports_bar_chart():
  # Get user id
  user_id = session.get("user_id")
  pie_data = (
    db.session.query(
      Category.name,
      db.func.coalesce(db.func.sum(Expense.amount), 0).label("total_spent")
    )
    .outerjoin(Expense, Expense.category_id==Category.id)
    .filter(Category.user_id==user_id)
    .group_by(Category.id, Category.name)
    .order_by(db.func.sum(Expense.amount).desc())
    .all()
  ) # Original adjusted by Copilot

  # Chart.js expects labels and a dataset array
  pie_labels = [row[0] for row in pie_data]
  pie_values = [float(row[1]) for row in pie_data]

  # BAR CHART DATA -> Will be called in reports route
  bar_data = (
    db.session.query(
      Category.name,
      db.func.coalesce(db.func.sum(BudgetEntry.budget_limit), 0).label("budget_limit")
    )
    .outerjoin(BudgetEntry, BudgetEntry.category_id==Category.id)
    .filter(Category.user_id==user_id)
    .group_by(Category.id, Category.name)
    .order_by(db.func.sum(BudgetEntry.budget_limit).desc())
    .all()
  )

  bar_labels = [row[0] for row in bar_data]
  bar_values = [float(row[1]) for row in bar_data]

  return jsonify({
    'pie': {
        'labels': pie_labels,
        'values': pie_values,
        'title': 'Expenses by Category',
    },
    'bar': {
        'labels': bar_labels,
        'values': bar_values,
        'title': 'Budget Entry by Category',
    },
    })


# reports
@app.route("/reports", methods=["GET"])
@login_required
def reports():
  return render_template("reports.html")

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
  user_id = session["user_id"]
  now = datetime.now()
  
  if request.method == "POST":
    income = request.form.get("income", type=float)
    action = request.form.get("action")
    
    # Validate inputs
    if not income:
      flash("Income is required")
      return redirect("/profile")

    if income <= 0:
      flash("Income must be greater than 0")
      return redirect("/profile")

    users = db.session.execute(select(User)).scalars().all()

    for user in users:
      if user.id == user_id:
        # store income in the Income db
        add_income = Income()
        add_income.user_id=user_id

        try:
          add_income.user_id=user_id
        except Exception:
          raise Exception
        
        #finally add income
        add_income.income_value=income
        # add to the db with JQuery
        if action == "save-income": 
          db.session.add(add_income)
          db.session.commit()
    return redirect("/profile")
  else:
    # use date for when user enters income
    date = now.strftime("%Y-%m")

    # fetch current user and their income (if any)
    users = db.session.query(User).filter(User.id == user_id).all()
    user_income = db.session.query(Income).filter(Income.user_id == user_id).first()

    return render_template("profile.html", users=users, user_income=user_income, date=date)


"""
  CRUD extensions for the expense route.
  Here we implement a delete expense and Edit expense
"""
@app.route("/delete-expense/<int:expense_id>", methods=["POST"])
@login_required
def delete(expense_id):
  user_id = session.get("user_id")
  if not user_id:
    return redirect("/login")
  
  # Query the expenses database
  res = (
    select(Expense)
    .join(Category)
    .where(Category.user_id==user_id, Expense.id==expense_id)
  )
  expense = db.session.execute(res).scalar_one_or_none()

  if expense:
    db.session.delete(expense)
    db.session.commit()

  return redirect("/expenses")

# Edit expense route
@app.route("/edit-expense/<int:expense_id>", methods=["GET", "POST"])
@login_required
def edit_expense(expense_id):
  user_id = session.get("user_id")

  res = (
    select(Expense)
    .join(Category)
    .where(Category.user_id == user_id, Expense.id == expense_id)
  )
  expense = db.session.execute(res).scalar_one_or_none()
  categories = Category.query.filter_by(user_id=user_id).all()

  if not expense:
    return redirect("/expenses")

  if request.method == "POST":
    income = request.form.get("income", type=float)
    expense = request.form.get("expense")
    merchant = request.form.get("merchant")
    category_name = request.form.get("category")
    amount = request.form.get("amount", type=float)   # amount spent on the expense
    currency = request.form.get("currency")
    modified_at = datetime.now().strftime("%Y-%m-%d")

    # validate inputs
    if not income:
      return redirect(f"/edit-expense/{expense_id}")
    if not expense:
      return redirect(f"/edit-expense/{expense_id}")
    if not merchant:
      return redirect(f"/edit-expense/{expense_id}")
    if not category_name:
      return redirect(f"/edit-expense/{expense_id}")
    if not amount:
      return redirect(f"/edit-expense/{expense_id}")
    if not currency:
      return redirect(f"/edit-expense/{expense_id}")
    
    # Check income
    if income is None:
      flash("Income is required")
      return redirect(f"/edit-expense/{expense_id}")
    if amount is None:
      flash("Amount is required")
      return redirect(f"/edit-expense/{expense_id}")
    
    if amount <= 0 or income <=0:
      flash("Amount must be greater than 0")
      return redirect(f"/edit-expense/{expense_id}")
    
    update_expense = Expense()
    update_expense.expense=expense
    update_expense.category=category_name
    update_expense.amount=amount
    update_expense.currency=currency
    update_expense.created_at=modified_at

    # Commit changes
    db.session.commit()
    return redirect("/expenses")

  return render_template("expense_form.html", mode="edit", expense=expense, categories=categories)


# Register / Sign up new user
@app.route("/register", methods=["GET", "POST"])
def sign_up():
  if request.method == "POST":
    email = request.form.get("email")
    password = request.form.get("password")
    confirm_password = request.form.get("confirm-password")

    print("EMAIL FORM FORM: ", repr(email))
    print("PASSWORD FROM FORM", repr(password))

    #action = request.form.get("register")

    # Validate the form inputs
    if not (email and password and confirm_password):
      flash("All fields are required")
      return redirect("/register")
    
    # ensure password matching -> validation
    if not password == confirm_password:
      flash("Passwords must match")
      return redirect("/register")

    # first select user by email
    user = db.session.query(User).filter_by(email=email).first()

    print("USER:", user)
    print("HASH:", user.password_hash if user else None)
    #rint("PASSWORD CHECK:", user.check_password(password))
    
    
    # store/insert the details in the database
    # check if user already exists in the User model, if not, add user
    if not user:
      #hashed_password = generate_password_hash(password)

      new_user = User()
      new_user.email=email
      new_user.set_password(password)
      print("PASSWORD CHECK:", new_user.check_password(password))


      #if action == "register":
      db.session.add(new_user)
      db.session.commit()
      return redirect("/login")
    else:
      flash(" User already exists")
      return redirect("/register")
  else: 
    return render_template("register.html")

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
  #session.clear()
  if request.method == "POST":
    email = request.form.get("email")
    password = request.form.get("password")

    # Validate user inputs (use a generic message to avoid revealing which field failed)
    if not email or not password:
      flash("Incorrect email and/or password")
      return redirect("/login")

    # Query a single user by email
    user = db.session.query(User).filter_by(email=email).first()

    # Verify user exists and password matches
    if user is None or not check_password_hash(user.password_hash, password):
      flash("Incorrect email and/or password")
      return redirect("/login")

    # Successful login
    session["user_id"] = user.id
    return redirect("/")
  # else GET route
  else:
    return render_template("login.html")
  
  # -------------------------------------------
#  Theme control
# Dark mode light mode features
@app.route("/toggle-theme")
def toggle_theme():
  current_theme = session.get("theme", "light")
  new_theme = "dark" if current_theme == "light" else "light"
  session["theme"] = new_theme
  #flash(f"Theme switched to {new_theme}.")
  ref = request.referrer or "/"
  return redirect(ref)

@app.context_processor
def inject_theme():
  return {"theme": session.get("theme", "light")}

# Logout -> on logout
@app.route("/logout")
def logout():
  session.clear()
  # redirect to login page
  return render_template("login.html")


# Always validate main
if __name__ == "__main__":
  app.run(debug=True)


"""
budgets = (
      db.session.query(BudgetEntry, Category)
      .join(Category, BudgetEntry.category_id == Category.id)
      .filter(Category.user_id == user_id)
      .all()
    )

    data = []

    for budget, category in budgets:
      # Calculate total_spent dynamically
      total_spent = db.session.query(
        db.func.sum(Expense.amount)  # assuming you have an Expense table linked to BudgetEntry
      ).filter(Expense.budget_entry_id==budget.id).scalar() or 0

      data.append({
        "id": budget.id,
        "name": category.name,
        "budget_limit": budget.budget_limit,
        "total_spent": total_spent,
        "remaining": budget.budget_limit - total_spent
      })

  return jsonify({"data": data}), 200
"""