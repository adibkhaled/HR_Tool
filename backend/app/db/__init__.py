from backend.app.db.base import Base

# Importing models here ensures `Base.metadata` is populated as soon as the database
# package is imported, even when callers reference `from backend.app.db.base import Base`.
from backend.app.models.models import *  # noqa: F401,F403

__all__ = ["Base"]
