"""
Customer and Address Models
Demonstrating Composition and Encapsulation.
"""

from typing import Dict, Any


class Address:
    """ที่อยู่สำหรับการจัดส่ง (Value Object / Component)"""

    def __init__(
        self,
        street: str,
        district: str,
        province: str,
        postal_code: str,
    ):
        self._street = street.strip()
        self._district = district.strip()
        self._province = province.strip()
        self._postal_code = postal_code.strip()

    @property
    def street(self) -> str:
        return self._street

    @property
    def district(self) -> str:
        return self._district

    @property
    def province(self) -> str:
        return self._province

    @property
    def postal_code(self) -> str:
        return self._postal_code

    def get_full_address(self) -> str:
        return f"{self._street}, เขต/อ.{self._district}, จ.{self._province} {self._postal_code}"

    def to_dict(self) -> Dict[str, str]:
        return {
            "street": self._street,
            "district": self._district,
            "province": self._province,
            "postal_code": self._postal_code,
            "full_address": self.get_full_address(),
        }

    def __str__(self) -> str:
        return self.get_full_address()


class Customer:
    """ข้อมูลลูกค้า (ผู้ส่ง / ผู้รับ)"""

    def __init__(
        self,
        customer_id: str,
        name: str,
        phone: str,
        email: str,
        address: Address,
    ):
        self._customer_id = customer_id
        self._name = name.strip()
        self._phone = phone.strip()
        self._email = email.strip()
        self._address = address  # Composition

    @property
    def customer_id(self) -> str:
        return self._customer_id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        if not value.strip():
            raise ValueError("ชื่อลูกค้าต้องไม่เว้นว่าง")
        self._name = value.strip()

    @property
    def phone(self) -> str:
        return self._phone

    @property
    def email(self) -> str:
        return self._email

    @property
    def address(self) -> Address:
        return self._address

    def to_dict(self) -> Dict[str, Any]:
        return {
            "customer_id": self._customer_id,
            "name": self._name,
            "phone": self._phone,
            "email": self._email,
            "address": self._address.to_dict(),
        }

    def __str__(self) -> str:
        return f"{self._name} ({self._phone})"
