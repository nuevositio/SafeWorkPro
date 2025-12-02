from __future__ import annotations

from typing import Dict


class CurrencyConverter:
    def __init__(self, base_currency: str = "USD", rates: Dict[str, float] | None = None):
        self.base_currency = base_currency.upper()
        self.rates = {self.base_currency: 1.0}
        if rates:
            for currency, rate in rates.items():
                self.rates[currency.upper()] = rate

    def convert_to_base(self, amount: float, currency: str) -> float:
        currency = currency.upper()
        if currency not in self.rates:
            raise ValueError(f"La moneda {currency} no tiene tasa de conversión configurada")
        return amount * self.rates[currency]
