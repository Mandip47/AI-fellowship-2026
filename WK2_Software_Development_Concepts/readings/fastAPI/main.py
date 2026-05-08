from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from models import Product
from database import session, engine
import database_models
from sqlalchemy.orm import Session

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # remove trailing slash
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

database_models.Base.metadata.create_all(bind=engine)

products = [
    Product(
        id=1,
        name="Laptop",
        description="A high-performance laptop",
        price=999.99,
        quantity=10,
    ),
    Product(
        id=2,
        name="Smartphone",
        description="A latest model smartphone",
        price=499.99,
        quantity=20,
    ),
    Product(
        id=3,
        name="Headphones",
        description="Noise-cancelling headphones",
        price=199.99,
        quantity=15,
    ),
    Product(
        id=4,
        name="Smartwatch",
        description="A smartwatch with various features",
        price=299.99,
        quantity=25,
    ),
]


def db_init():
    db = session()
    try:
        for product in products:
            # skip insert if product with same PK already exists
            if not db.get(database_models.Product, product.id):
                db_product = database_models.Product(**product.model_dump())
                db.add(db_product)
        db.commit()
    finally:
        db.close()


db_init()


def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def test():
    return {"data": "Hello World"}


@app.get("/products/")
def get_products(db: Session = Depends(get_db)):
    # dbconnectoin
    # db = session()
    # query
    products = db.query(database_models.Product).all()
    return products


@app.get("/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    # db_product = db.get(database_models.Product, product_id)
    db_product = (
        db.query(database_models.Product)
        .filter(database_models.Product.id == product_id)
        .first()
    )
    if db_product:
        return db_product

    return {"error": "Product not found"}


@app.post("/products/")
def create_product(product: Product, db: Session = Depends(get_db)):
    db_product = database_models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()

    # products.append(product)
    return product


@app.put("/products/{product_id}")
def update_product(product_id: int, product: Product, db: Session = Depends(get_db)):
    db_product = db.get(database_models.Product, product_id)
    if db_product:
        db_product.name = product.name
        db_product.description = product.description
        db_product.price = product.price
        db_product.quantity = product.quantity
        db.commit()
        return db_product

    return {"error": "Product not found"}


@app.delete("/products/{id}")
def delete_product(id: int, db: Session = Depends(get_db)):
    db_product = db.get(database_models.Product, id)
    if db_product:
        db.delete(db_product)
        db.commit()
        return {"message": "Product deleted"}

    # for idx, product in enumerate(products):
    #     if product.id == product_id:
    #         del products[idx]
    #         return {"message": "Product deleted"}
    return {"error": "Product not found"}
