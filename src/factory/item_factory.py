"""
Factory Pattern Implementation for Creating Items/Parcels
Encapsulates object instantiation and validation according to parcel classification.
"""

import uuid
from typing import Dict, Any, Union
from ..models.item import (
    Item,
    ItemType,
    StandardParcel,
    FragileParcel,
    PerishableParcel,
    HazardousParcel,
    CushioningLevel,
)


class ItemFactory:
    """
    Factory Pattern สำหรับสร้าง Object สินค้าและพัสดุประเภทต่างๆ
    ช่วยลดความซับซ้อนและการผูกติด (Loose Coupling) ระหว่าง UI/Service กับ Concrete Class
    """

    @staticmethod
    def create_item(item_type: Union[ItemType, str], **kwargs: Any) -> Item:
        """
        สร้างอินสแตนซ์ของ Item ตามประเภทที่ระบุ

        :param item_type: ประเภทของสินค้า (STANDARD, FRAGILE, PERISHABLE, HAZARDOUS)
        :param kwargs: พารามิเตอร์ตามคุณสมบัติเฉพาะของประเภทนั้น
        :return: อินสแตนซ์ของ Item ที่สืบทอดถูกต้อง
        """
        if isinstance(item_type, str):
            try:
                item_type = ItemType(item_type.upper())
            except ValueError:
                valid_types = [t.value for t in ItemType]
                raise ValueError(f"ไม่รู้จักประเภทสินค้า '{item_type}'. ประเภทที่ถูกต้อง: {valid_types}")

        item_id = kwargs.get("item_id") or f"ITM-{uuid.uuid4().hex[:8].upper()}"
        name = kwargs.get("name", "Unnamed Parcel")
        weight = float(kwargs.get("weight", 1.0))
        volume = float(kwargs.get("volume", 0.01))
        declared_value = float(kwargs.get("declared_value", 0.0))

        if item_type == ItemType.STANDARD:
            return StandardParcel(
                item_id=item_id,
                name=name,
                weight=weight,
                volume=volume,
                declared_value=declared_value,
            )

        elif item_type == ItemType.FRAGILE:
            cushioning_raw = kwargs.get("cushioning_level", CushioningLevel.STANDARD)
            if isinstance(cushioning_raw, str):
                try:
                    cushioning = CushioningLevel(cushioning_raw)
                except ValueError:
                    cushioning = CushioningLevel.STANDARD
            else:
                cushioning = cushioning_raw

            requires_insurance = bool(kwargs.get("requires_insurance", True))

            return FragileParcel(
                item_id=item_id,
                name=name,
                weight=weight,
                volume=volume,
                declared_value=declared_value,
                cushioning_level=cushioning,
                requires_insurance=requires_insurance,
            )

        elif item_type == ItemType.PERISHABLE:
            target_temp = float(kwargs.get("target_temperature_celsius", 4.0))
            expiry_hours = int(kwargs.get("expiry_hours", 48))

            return PerishableParcel(
                item_id=item_id,
                name=name,
                weight=weight,
                volume=volume,
                declared_value=declared_value,
                target_temperature_celsius=target_temp,
                expiry_hours=expiry_hours,
            )

        elif item_type == ItemType.HAZARDOUS:
            hazard_class = str(kwargs.get("hazard_class", "Class 3 (Flammable Liquids)"))
            safety_license_id = str(kwargs.get("safety_license_id", "HAZ-CERT-DEFAULT"))

            return HazardousParcel(
                item_id=item_id,
                name=name,
                weight=weight,
                volume=volume,
                declared_value=declared_value,
                hazard_class=hazard_class,
                safety_license_id=safety_license_id,
            )

        else:
            raise ValueError(f"ไม่รองรับประเภทสินค้า: {item_type}")
