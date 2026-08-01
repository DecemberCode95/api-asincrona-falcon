from pydantic import BaseModel, Field

class ProductoSchema(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=50)
    precio: float = Field(..., gt=0)
    en_stock: bool

class LoginSchema(BaseModel):
    usuario: str
    password: str

    