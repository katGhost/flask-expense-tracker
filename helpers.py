#import requests
from flask import redirect, render_template, session, flash
from functools import wraps

# simple login_required decorator using session
def login_required(f):
  @wraps(f)
  def decorated_function(*args, **kwargs):
    if session.get("user_id") is None:
      return redirect("/login")
    return f(*args, **kwargs)
  return decorated_function

#def usd(value):
#  return f"${value:,.2f}"