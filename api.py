from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Product(BaseModel):
    title: str
    price: float
    in_stock: bool

products = []

@app.post("/products")
async def create_product(product: Product):
    products.append(product)
    return {"message": "Product created", "product": product}