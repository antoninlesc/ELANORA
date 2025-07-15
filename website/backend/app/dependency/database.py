from fastapi import Depends

from app.db.database import get_db

get_db_dep = Depends(get_db)
