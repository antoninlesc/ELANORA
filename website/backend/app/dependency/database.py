from db.database import get_db
from fastapi import Depends

get_db_dep = Depends(get_db)
