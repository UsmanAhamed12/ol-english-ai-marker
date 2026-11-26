"""Dependencies every route can ask for.

Routes write ``user: User = Depends(get_current_user)`` and
``db: Session = Depends(get_db)``; both come from here so there is one place to
change how a request is authenticated or how a database session is opened.
"""

from app.core.security import get_current_user
from app.db import get_db

__all__ = ["get_db", "get_current_user"]