import datetime
from typing import Optional
from app.models import Delivery, DeliveryStatus, OrderStatus, Orders, Restaurant, db, Offer


def get_user(login: str, password: str) -> Optional[Restaurant]:
    # This function should return the user id if the login and password are correct, otherwise return None
    user = Restaurant.query.filter_by(login=login, password=password).first()
    return user

def get_not_finished_orders(restaurant_id: int) -> dict[OrderStatus, list[Orders]]:
    orders = (db.session.query(Orders)
             .join(Offer)
             .filter(Offer.restaurant_id == restaurant_id)
            #  .filter(~Orders.orderStatus.in_([OrderStatus.Delivered, OrderStatus.InDelivery, OrderStatus.Canceled]))
             .all())

    # Group orders by status
    orders_by_status = {
        OrderStatus.Registered: [],
        OrderStatus.InPreparation: [],
        OrderStatus.WaitingForDelivery: [],
        OrderStatus.Delivered: [],
        OrderStatus.Canceled: []
    }
    
    for order in orders:
        orders_by_status[order.orderStatus].append(order)
    return orders_by_status

def get_order(order_id: int, restaurant_id: int) -> Orders | None:
    return (db.session.query(Orders)
             .join(Offer)
             .filter(Offer.restaurant_id == restaurant_id and Orders.id == order_id)
             .first())

def update_order_with_delivery(self, order_id: int, deliverer_id: int, notes: Optional[str] = None) -> Orders:
    order = Orders.query.get_or_404(order_id)
    
    # Create new delivery
    delivery = Delivery(
        order_id=order_id,
        deliverer_id=deliverer_id,
        deliveryStatus=DeliveryStatus.Waiting,
        deliveryDue=datetime.now() + timedelta(hours=1),
        deliveryTime=datetime.now()
    )
    
    # Update order status and notes
    order.orderStatus = OrderStatus.WaitingForDelivery
    if notes is not None:
        order.notes = notes
        
    self.db.session.add(delivery)
    self.db.session.commit()
    return order
    
def get_available_deliverers(self, restaurant_id: int) -> List[Deliverer]:
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    return restaurant.deliverers.all()

def update_order(self, order_id: int, status: str, notes: Optional[str] = None) -> Orders:
    order = Orders.query.get_or_404(order_id)
    order.orderStatus = OrderStatus(status)
    
    if notes is not None:
        order.notes = notes
        
    # If order is ready and no delivery required, mark as delivered
    if status == OrderStatus.WaitingForDelivery.value and not order.offer.request.withDelivery:
        order.orderStatus = OrderStatus.Delivered
        
    self.db.session.commit()
    return order