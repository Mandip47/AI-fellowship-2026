from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ProductLine(Base):
    __tablename__ = "productlines"
    id = Column(Integer, primary_key=True)
    productLine = Column(String(50), unique=True, nullable=False)
    textDescription = Column(Text)
    htmlDescription = Column(Text)


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    productCode = Column(String(15), unique=True, nullable=False)
    productName = Column(String(70), nullable=False)
    productLine_id = Column(Integer, ForeignKey("productlines.id"))
    productScale = Column(String(10))
    productVendor = Column(String(50))
    productDescription = Column(Text)
    quantityInStock = Column(Integer)
    buyPrice = Column(Float)
    MSRP = Column(Float)
    productLine = relationship("ProductLine")


class Office(Base):
    __tablename__ = "offices"
    id = Column(Integer, primary_key=True)
    officeCode = Column(String(10), unique=True, nullable=False)
    city = Column(String(50), nullable=False)
    phone = Column(String(50))
    addressLine1 = Column(String(50))
    addressLine2 = Column(String(50))
    state = Column(String(50))
    country = Column(String(50), nullable=False)
    postalCode = Column(String(15))
    territory = Column(String(10))


class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    employeeNumber = Column(Integer, unique=True, nullable=False)
    lastName = Column(String(50), nullable=False)
    firstName = Column(String(50), nullable=False)
    extension = Column(String(10))
    email = Column(String(100))
    office_id = Column(Integer, ForeignKey("offices.id"))
    reportsTo = Column(Integer, ForeignKey("employees.id"))
    jobTitle = Column(String(50))
    office = relationship("Office")


class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    customerNumber = Column(Integer, unique=True, nullable=False)
    customerName = Column(String(50), nullable=False)
    contactLastName = Column(String(50))
    contactFirstName = Column(String(50))
    phone = Column(String(50))
    addressLine1 = Column(String(50))
    addressLine2 = Column(String(50))
    city = Column(String(50))
    state = Column(String(50))
    postalCode = Column(String(15))
    country = Column(String(50))
    salesRep_id = Column(Integer, ForeignKey("employees.id"))
    creditLimit = Column(Float)
    salesRep = relationship("Employee")


class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    checkNumber = Column(String(50), unique=True, nullable=False)
    paymentDate = Column(Date, nullable=False)
    amount = Column(Float, nullable=False)
    customer = relationship("Customer")


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    orderNumber = Column(Integer, unique=True, nullable=False)
    orderDate = Column(Date, nullable=False)
    requiredDate = Column(Date)
    shippedDate = Column(Date)
    status = Column(String(15))
    comments = Column(Text)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    customer = relationship("Customer")


class OrderDetail(Base):
    __tablename__ = "orderdetails"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantityOrdered = Column(Integer, nullable=False)
    priceEach = Column(Float, nullable=False)
    orderLineNumber = Column(Integer)
    order = relationship("Order")
    product = relationship("Product")
