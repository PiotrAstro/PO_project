import datetime
from typing import Optional
from app.models import Deliverer, Delivery, DeliveryStatus, OrderStatus, Orders, Restaurant, db, Offer


def get_user(login: str, password: str) -> Optional[Restaurant]:
    # This function should return the user id if the login and password are correct, otherwise return None
    user = Restaurant.query.filter_by(login=login, password=password).first()
    return user

def get_orders(restaurant_id: int) -> dict[OrderStatus, list[Orders]]:
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
        OrderStatus.InDelivery: [],
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

def update_order(order_id: int, restaurant_id: int, status: str, notes: Optional[str] = None) -> Orders:
    order = (db.session.query(Orders)
             .join(Offer)
             .filter(Offer.restaurant_id == restaurant_id and Orders.id == order_id)
             .first())
    assert order is not None
    order.orderStatus = OrderStatus(status)
    
    if notes is not None:
        order.notes = notes
        
    # If order is ready and no delivery required, mark as delivered
    if status == OrderStatus.WaitingForDelivery.value and not order.offer.request.withDelivery:
        order.orderStatus = OrderStatus.Delivered
        
    db.session.commit()
    return order

def update_order_with_delivery(order_id: int, deliverer_id: int, delivery_due: datetime.datetime, notes: Optional[str] = None) -> Orders:
    order = Orders.query.get_or_404(order_id)
    
    # Create new delivery
    delivery = Delivery(
        order_id=order_id,
        deliverer_id=deliverer_id,
        deliveryStatus=DeliveryStatus.Waiting,
        deliveryDue=delivery_due,
    )
    
    # Update order status and notes
    order.orderStatus = OrderStatus.InDelivery
    if notes is not None:
        order.notes = notes
        
    db.session.add(delivery)
    db.session.commit()
    return order

def cancel_order(order_id: int, restaurant_id: int) -> Orders:
    order = (db.session.query(Orders)
             .join(Offer)
             .filter(Offer.restaurant_id == restaurant_id and Orders.id == order_id)
             .first())
    assert order is not None
    order.orderStatus = OrderStatus.Canceled
    db.session.commit()
    return order

def get_available_deliverers(restaurant_id: int) -> list[tuple[int, str]]:
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    return restaurant.deliverers