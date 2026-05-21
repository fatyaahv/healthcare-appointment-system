from __future__ import annotations

import json
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen


class HolidayService:
    """Small external REST integration used by the API demo."""

    BASE_URL = "https://date.nager.at/api/v3/PublicHolidays"

    def get_public_holidays(self, year: int, country_code: str = "TR") -> dict[str, Any]:
        country_code = country_code.upper()
        url = f"{self.BASE_URL}/{year}/{country_code}"
        try:
            with urlopen(url, timeout=5) as response:
                holidays = json.loads(response.read().decode("utf-8"))
            source = url
        except (OSError, URLError, TimeoutError, json.JSONDecodeError):
            holidays = self._offline_fallback(year, country_code)
            source = "offline fallback"

        return {
            "source": source,
            "year": year,
            "countryCode": country_code,
            "holidays": [
                {
                    "date": item.get("date", ""),
                    "localName": item.get("localName", ""),
                    "name": item.get("name", ""),
                }
                for item in holidays
            ],
        }

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
