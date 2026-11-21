"""Reglas de dominio independientes de Tkinter y PostgreSQL."""
from dataclasses import dataclass
from datetime import date
from typing import Protocol

class BusinessError(ValueError):
    pass

@dataclass(frozen=True)
class OrderLine:
    product: str
    quantity: int

@dataclass(frozen=True)
class FinalLine:
    product: str
    produced: int
    lost: int
    reason: str = ''

def integer(value, label, minimum=0, maximum=999):
    try:
        text = str(value).strip()
        if not text.isascii() or not text.isdecimal():
            raise ValueError()
        result = int(text)
    except (ValueError, TypeError):
        raise BusinessError(f'{label}: ingrese un número entero entre {minimum} y {maximum}.')
    if not minimum <= result <= maximum:
        raise BusinessError(f'{label}: debe estar entre {minimum} y {maximum}.')
    return result

def validate_order(day, employee, lines):
    try:
        parsed = date.fromisoformat(day)
        if parsed.isoformat() != day:
            raise ValueError()
    except (TypeError, ValueError):
        raise BusinessError('Fecha inválida. Use AAAA-MM-DD.')
    if not employee:
        raise BusinessError('Seleccione un responsable.')
    if not lines:
        raise BusinessError('Agregue al menos un producto.')
    if len({x.product for x in lines}) != len(lines):
        raise BusinessError('Cada producto debe aparecer una sola vez.')
    for line in lines:
        if not line.product:
            raise BusinessError('Seleccione un producto válido.')
        integer(line.quantity, 'Cantidad programada', 1)

def validate_close(planned, results):
    if not planned or len(results) != len(planned) or {x.product for x in results} != set(planned):
        raise BusinessError('Registre el resultado de todos los productos, sin duplicados.')
    for line in results:
        integer(line.produced, 'Cantidad producida')
        integer(line.lost, 'Cantidad perdida')
        if line.produced + line.lost != planned[line.product]:
            raise BusinessError(f'{line.product}: producida + perdida debe ser igual a la programada ({planned[line.product]}).')
        if line.lost and not line.reason.strip():
            raise BusinessError(f'{line.product}: indique el motivo de la merma.')
        if len(line.reason.strip()) > 80:
            raise BusinessError('El motivo admite un máximo de 80 caracteres.')
        if not line.lost and line.reason.strip():
            raise BusinessError(f'{line.product}: quite el motivo si no existe merma.')

class OrderRepository(Protocol):
    def save(self, number, day, employee, lines): ...
    def start(self, number): ...
    def cancel(self, number): ...
    def close(self, number, results): ...

class ProductionService:
    def __init__(self, repository: OrderRepository):
        self.repository = repository

    def save(self, number, day, employee, lines):
        validate_order(day, employee, lines)
        return self.repository.save(number, day, employee, lines)

    def start(self, number):
        self.repository.start(number)

    def cancel(self, number):
        self.repository.cancel(number)

    def close(self, number, results):
        self.repository.close(number, results)
