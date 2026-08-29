from enum import Enum, StrEnum


class UserRole(str, Enum):
    ADMIN = "admin"
    DRIVER = "driver"



class RouteStatus(str, Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    



class DeliveryStatus(str, Enum):
    PENDING = "pending"
    ON_WAY = "on_way"
    DELIVERED = "delivered"
    FAILED = "failed"

class OrderPurpose(str, Enum):
    DELIVERY_19L = "delivery_19l"   # доставка капсул 19 л — поведение по умолчанию
    PICKUP = "pickup"               # вывоз кулера и/или капсул заказчика
    BULK_WATER = "bulk_water"       # опт 5 л / 10 л, цена договорная


class ExpenseCategory(str, Enum):
    FUEL = "fuel"
    LUNCH = "lunch"
    REPAIR = "repair"
    OTHER = "other"



class NotificationType(str, Enum):
    DELIVERY_STATUS_UPDATED = "delivery_status_updated"
    DELIVERY_COMPLETED = "delivery_completed"
    ROUTE_COMPLETED = "route_completed"
    ROUTE_UPDATED = "route_updated"
    CUSTOMER_REMOVED = "customer_removed"
    ROUTE_CANCELLED = "route_cancelled"
    CUSTOMER_ADDED = "customer_added"
    


class PaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"
    TRANSFER = "transfer"
    DEBT = "debt"
