from functools import wraps
from flask import session, request, redirect, url_for

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
          if session["user_id"] is None:
              return redirect('/register')
          return f(*args, **kwargs)
        except:
          return redirect('/register')
        return f(*args, **kwargs)
    return decorated_function