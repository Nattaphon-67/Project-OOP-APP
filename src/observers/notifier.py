"""
Observer Pattern Implementation for Shipment Tracking & Alerts
Notifies customers and logs audit trails when shipment status changes.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..models.shipment import Shipment, TrackingEvent


class ShipmentObserver(ABC):
    """
    Observer Interface (Subscriber)
    """

    @abstractmethod
    def on_status_changed(self, shipment: Shipment, event: TrackingEvent) -> None:
        """ทำงานเมื่อสถานะพัสดุเกิดการเปลี่ยนแปลง"""
        pass


class CustomerSMSNotifier(ShipmentObserver):
    """ส่งการแจ้งเตือนทาง SMS จำลองไปยังผู้รับและผู้ส่ง"""

    def __init__(self):
        self._sent_messages: List[Dict[str, str]] = []

    @property
    def sent_messages(self) -> List[Dict[str, str]]:
        return list(self._sent_messages)

    def on_status_changed(self, shipment: Shipment, event: TrackingEvent) -> None:
        text = (
            f"[SMS Alert] พัสดุ {shipment.tracking_number} ({shipment.item.name}) "
            f"สถานะ: {event.status.value} ณ {event.location} - {event.message}"
        )
        self._sent_messages.append({
            "to_recipient": shipment.receiver.phone,
            "to_sender": shipment.sender.phone,
            "message": text,
            "timestamp": event.timestamp,
        })


class CustomerEmailNotifier(ShipmentObserver):
    """ส่งอีเมลอัปเดตความคืบหน้าจำลอง"""

    def __init__(self):
        self._sent_emails: List[Dict[str, str]] = []

    @property
    def sent_emails(self) -> List[Dict[str, str]]:
        return list(self._sent_emails)

    def on_status_changed(self, shipment: Shipment, event: TrackingEvent) -> None:
        subject = f"อัปเดตสถานะพัสดุ #{shipment.tracking_number}: {event.status.value}"
        body = (
            f"เรียน คุณ{shipment.receiver.name},\n"
            f"พัสดุของคุณได้รับการอัปเดตสถานะเป็น: {event.status.value}\n"
            f"สถานที่: {event.location}\n"
            f"ข้อความ: {event.message}\n"
            f"เวลา: {event.timestamp}"
        )
        self._sent_emails.append({
            "to": shipment.receiver.email,
            "subject": subject,
            "body": body,
            "timestamp": event.timestamp,
        })


class SystemAuditLogger(ShipmentObserver):
    """บันทึกเหตุการณ์ลงระบบ Audit Log"""

    def __init__(self):
        self._logs: List[str] = []

    @property
    def logs(self) -> List[str]:
        return list(self._logs)

    def on_status_changed(self, shipment: Shipment, event: TrackingEvent) -> None:
        log_entry = (
            f"AUDIT | {event.timestamp} | TRACKING={shipment.tracking_number} | "
            f"TYPE={shipment.item.get_item_type().value} | STATUS={event.status.value} | "
            f"LOC={event.location} | MSG={event.message}"
        )
        self._logs.append(log_entry)


class NotificationManager:
    """
    Subject / Observable Manager
    จัดการการลงทะเบียนผู้ฟัง (Observers) และการกระจายข่าวสาร (Publish)
    """

    def __init__(self):
        self._observers: List[ShipmentObserver] = []

    def subscribe(self, observer: ShipmentObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def unsubscribe(self, observer: ShipmentObserver) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, shipment: Shipment, event: TrackingEvent) -> None:
        """กระจายการแจ้งเตือนไปยัง Observers ทั้งหมด"""
        for obs in self._observers:
            try:
                obs.on_status_changed(shipment, event)
            except Exception as e:
                print(f"[Notifier Error] {e}")
