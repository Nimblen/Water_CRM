from enum import Enum


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
    PAID = "paid"