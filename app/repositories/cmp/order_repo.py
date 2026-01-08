from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.cmp.order import Order
from app.models.cmp.order_detail import OrderDetail

class OrderRepo:
    def __init__(self, db: Session):
        self.db = db

    # 创建订单
    def create(self, data: Order):
        # order_db = Order(**data)
        self.db.add(data)
        self.db.flush()
        return data


    # 查找订单
    def get_last_product_order(self, instance_id: str):
        return self.db.query(Order).filter(Order.instance_id == instance_id).first()


class OrderDetailRepo:
    def __init__(self, db: Session):
        self.db = db

    # 创建明细
    def create(self, data: OrderDetail):
        # detail_db = OrderDetail(**data)
        self.db.add(data)
        self.db.flush()
        return data