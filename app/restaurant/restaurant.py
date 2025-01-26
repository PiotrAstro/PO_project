import datetime
from typing import Optional
from app.models import Deliverer, Delivery, DeliveryStatus, OrderStatus, Orders, Restaurant, db, Offer
from sqlalchemy import text


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
             .filter(Offer.restaurant_id == restaurant_id)
             .filter(Orders.id == order_id)
             .first())

def update_order(order_id: int, restaurant_id: int, status: str, notes: Optional[str] = None) -> Orders:
    order = (db.session.query(Orders)
             .join(Offer)
             .filter(Offer.restaurant_id == restaurant_id)
             .filter(Orders.id == order_id)
             .first())
    assert order is not None
    print(order)
    order_status = OrderStatus[status]
    print(order_status)
    if notes is not None:
        order.notes = notes
    print(notes)
    order.orderStatus = order_status
    print(order.orderStatus)
    db.session.commit()
    select_same_order = Orders.query.get(order_id)
    print(select_same_order)
    print(select_same_order.orderStatus)
    return order

def update_order_with_delivery(order_id: int, deliverer_id: int, delivery_due: datetime.datetime, notes: Optional[str] = None) -> Orders:
    order = Orders.query.get_or_404(order_id)
    
    # Create new delivery
    delivery = Delivery(
        order_id=order_id,
        deliverer_id=deliverer_id,
        deliveryStatus=DeliveryStatus.InDelivery,
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
             .filter(Offer.restaurant_id == restaurant_id)
             .filter(Orders.id == order_id)
             .first())
    assert order is not None
    order.orderStatus = OrderStatus.Canceled
    db.session.commit()
    return order

def get_available_deliverers(restaurant_id: int) -> list[tuple[int, str]]:
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    return restaurant.deliverers


def get_available_requests(restaurant_id: int):
    """
    Zwraca listę dostępnych 'requestów' (zapytań) złożonych przez klientów,
    dla których restauracja może złożyć ofertę (czyli takich, gdzie nie ma jeszcze
    innej oferty zaakceptowanej lub przypisanej do zamówienia).
    """
    sql = text('''
        SELECT r.id AS request_id,
               c.name || ' ' || c.surname AS client_name,
               string_agg(ri.name, ', ') AS ordered_items,
               r."withDelivery",
               r.address,
               r."electronicPayment"
        FROM "Request" r
        JOIN "Client" c ON r.client_id = c.id
        JOIN "RecipeRequest" rr ON r.id = rr.request_id
        JOIN "Recipe" ri ON rr.recipe_id = ri.id
        WHERE r.id NOT IN (
            SELECT o.request_id
            FROM "Offer" o
            LEFT JOIN "Orders" ord ON o.id = ord.offer_id
            WHERE ord.id IS NOT NULL
        )
        AND r.id NOT IN (
            SELECT o.request_id
            FROM "Offer" o
            WHERE o.restaurant_id = :restaurant_id
        )
        GROUP BY r.id, c.name, c.surname, r."withDelivery", r.address, r."electronicPayment"
    ''')
    return db.session.execute(sql, {'restaurant_id': restaurant_id}).fetchall()


def create_offer(restaurant_id: int, request_id: int, price: float, notes: str, waiting_time: str):
    """
    Tworzy ofertę (Offer) dla konkretnego requestu.
    """
    sql = text('''
        INSERT INTO "Offer" (request_id, restaurant_id, price, notes, "waitingTime")
        VALUES (:request_id, :restaurant_id, :price, :notes, :waiting_time)
    ''')
    db.session.execute(sql, {
        'request_id': request_id,
        'restaurant_id': restaurant_id,
        'price': price,
        'notes': notes,
        'waiting_time': waiting_time
    })
    db.session.commit()