from __future__ import annotations

from typing import Any
from urllib.request import urlopen
from xml.etree import ElementTree as ET


class HolidayService:
    """External XML service adapter with a local fallback for offline demos."""

    def get_public_holidays(self, year: int, country_code: str = "TR") -> dict[str, Any]:
        country_code = country_code.upper()
        exchange_rates = self._tcmb_exchange_rates()
        return {
            "source": "TCMB external XML service" if exchange_rates else "local XML-compatible holiday data",
            "year": year,
            "countryCode": country_code,
            "holidays": self._offline_fallback(year, country_code),
            "externalExchangeRates": exchange_rates,
        }

    def _tcmb_exchange_rates(self) -> list[dict[str, str]]:
        try:
            with urlopen("https://www.tcmb.gov.tr/kurlar/today.xml", timeout=3) as response:
                root = ET.fromstring(response.read())
        except Exception:
            return []

        rates = []
        for currency in root.findall("Currency")[:5]:
            rates.append(
                {
                    "code": currency.attrib.get("CurrencyCode", ""),
                    "name": self._node_text(currency, "Isim"),
                    "forexBuying": self._node_text(currency, "ForexBuying"),
                    "forexSelling": self._node_text(currency, "ForexSelling"),
                }
            )
        return rates

    def _node_text(self, parent: ET.Element, tag: str) -> str:
        node = parent.find(tag)
        return node.text.strip() if node is not None and node.text else ""

    def _offline_fallback(self, year: int, country_code: str) -> list[dict[str, str]]:
        if country_code != "TR":
            return []
        return [
            {"date": f"{year}-01-01", "localName": "Yilbasi", "name": "New Year's Day"},
            {"date": f"{year}-04-23", "localName": "Ulusal Egemenlik ve Cocuk Bayrami", "name": "National Sovereignty and Children's Day"},
            {"date": f"{year}-05-01", "localName": "Emek ve Dayanisma Gunu", "name": "Labour and Solidarity Day"},
            {"date": f"{year}-05-19", "localName": "Ataturk'u Anma, Genclik ve Spor Bayrami", "name": "Commemoration of Ataturk, Youth and Sports Day"},
            {"date": f"{year}-07-15", "localName": "Demokrasi ve Milli Birlik Gunu", "name": "Democracy and National Unity Day"},
            {"date": f"{year}-08-30", "localName": "Zafer Bayrami", "name": "Victory Day"},
            {"date": f"{year}-10-29", "localName": "Cumhuriyet Bayrami", "name": "Republic Day"},
        ]
