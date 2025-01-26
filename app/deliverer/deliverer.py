from typing import Optional
from app.models import Deliverer, Delivery, DeliveryStatus, OrderStatus, Orders, db


def get_user(login: str, password: str) -> Optional[Deliverer]:
    # This function should return the user id if the login and password are correct, otherwise return None
    user = Deliverer.query.filter_by(login=login, password=password).first()
    return user

def get_deliveries_by_status(deliverer_id: int) -> dict[DeliveryStatus, list[Delivery]]:
    deliveries_by_status = {
        DeliveryStatus.InDelivery: [],
        DeliveryStatus.Delivered: [],        
    }
    deliveries = Delivery.query.filter_by(deliverer_id=deliverer_id).all()

    for delivery in deliveries:
        deliveries_by_status[delivery.deliveryStatus].append(delivery)

    return deliveries_by_status

def delivery_done(deliverer_id, delivery_id):
    delivery = Delivery.query.filter_by(id=delivery_id, deliverer_id=deliverer_id).first()
    assert delivery is not None
    delivery.deliveryStatus = DeliveryStatus.Delivered
    delivery.deliveryTime = db.func.current_timestamp()
    given_order_status = Orders.query.get(delivery.order_id)
    assert given_order_status is not None
    given_order_status.orderStatus = OrderStatus.Delivered
    db.session.commit()
    return delivery