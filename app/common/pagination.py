from typing import Tuple
from sqlalchemy.orm import Query

def paginate_query(query: Query, page: int, page_size: int) -> Tuple[int, list]:
    total = query.order_by(None).count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return total, items
