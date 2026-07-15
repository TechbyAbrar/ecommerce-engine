# 🛒 E-commerce Engine — Backend API

A production-oriented **E-commerce Ordering & Payment Backend System** built with **FastAPI, SQLAlchemy 2.0, PostgreSQL, and modern Python engineering practices**.

This project demonstrates scalable backend architecture with secure authentication, payment provider abstraction, transactional order processing, category-based recommendation algorithms, caching strategies, and a design prepared for future microservice migration.

---

## 🚀 Tech Stack

### Backend

* **FastAPI** — High-performance REST API framework
* **Python 3.12+**
* **SQLAlchemy 2.0** — Modern ORM with async-ready architecture
* **Pydantic v2** — Data validation and serialization
* **Alembic** — Database migration management
* **PostgreSQL** — Primary relational database
* **Neon PostgreSQL** — Cloud database with live monitoring and observability
* **Redis** — Caching layer
* **UV** — Modern Python package manager and dependency management

### Security

* **Argon2 Password Hashing** — Modern password security standard
* JWT-based authentication
* Secure environment-based configuration
* API rate limiting
* Input validation with Pydantic schemas

### Development & Operations

* Docker support
* Swagger / OpenAPI documentation
* Structured logging
* CLI-based technical administration
* Automated testing support

---

# 🏗️ Architecture Overview

The project follows a layered architecture designed for maintainability and future service separation.

```
app/
│
├── api/              # REST API routes
│
├── core/             # Application configuration, security, constants
│
├── models/           # SQLAlchemy database models
│
├── schemas/          # Pydantic request/response models
│
├── repositories/     # Database access layer
│
├── services/         # Business logic layer
│
├── strategies/       # Payment provider strategies
│
├── utils/            # Shared utilities
│
├── cli/              # Technical administration commands
│
└── tests/            # Automated tests
```

### Why this architecture?

The separation between API, service, and repository layers keeps business logic independent from infrastructure.

This makes the system easier to:

* Scale horizontally
* Add new payment providers
* Extract services into microservices
* Maintain large development teams
* Replace infrastructure components

---

# ✨ Key Engineering Features

## 🔐 Modern Authentication & Security

Implemented secure authentication using:

* JWT authentication
* Argon2 password hashing
* Environment-based secrets management
* Request validation
* API rate limiting

### Why Argon2 instead of bcrypt?

Argon2 provides stronger resistance against modern brute-force and GPU-based attacks by using memory-hard hashing algorithms.

---

# 📦 Product Management

Features:

* Product CRUD operations
* SKU uniqueness validation
* Stock management
* Product status handling
* Category relationships
* Indexed database fields for optimized queries

Example product structure:

```
Product
 ├── id
 ├── name
 ├── sku
 ├── price
 ├── stock
 ├── status
 └── timestamps
```

---

# 🛍️ Order Management System

The order system follows transactional business rules.

Flow:

```
User
 |
Select Products
 |
Create Order
 |
Choose Payment Provider
 |
Payment Confirmation
 |
Stock Reduction
 |
Order Completed
```

Implemented:

* Multiple products per order
* Order item calculation
* Subtotal calculation
* Total amount calculation
* Transaction-safe stock reduction
* Idempotent order operations

---

# 💳 Payment Architecture

Payment processing uses the **Strategy Design Pattern**.

Instead of coupling order logic with payment providers:

```
                Payment Interface
                       |
        --------------------------------
        |                              |
     Stripe                         bKash
```

Adding a new provider only requires implementing a new strategy.

Example future providers:

* PayPal
* SSLCommerz
* Razorpay
* Apple Pay

No modification required in core order processing.

---

# 🔄 Idempotent API Design

Critical payment and order operations are designed to prevent duplicate processing.

Examples:

* Duplicate payment callbacks
* Repeated webhook delivery
* Multiple checkout requests

Benefits:

* Prevents duplicate transactions
* Improves payment reliability
* Handles distributed system failures safely

---

# 🌳 Category Recommendation System (DFS + Redis)

Implemented category hierarchy traversal using **Depth First Search (DFS)**.

Example:

```
Electronics
 |
 ├── Mobile
 │     ├── Android
 │     └── iPhone
 |
 └── Laptop
```

DFS is used to efficiently traverse related categories and discover recommended products.

Optimization:

```
Database
    |
    ↓
Category Tree
    |
    ↓
Redis Cache
    |
    ↓
Fast Recommendation Queries
```

Benefits:

* Reduced database queries
* Faster repeated category traversal
* Better scalability

---

# 🗄️ Database Design

Database entities:

```
Users
 |
 └── Orders
        |
        └── OrderItems
                |
                └── Products


Orders
 |
 └── Payments


Categories
 |
 └── Products
```

Database improvements:

* Proper foreign key relationships
* Indexed fields
* Normalized schema
* Migration-based database changes

---

# 🖥️ Technical Admin CLI

The project includes CLI utilities for backend operations.

Examples:

* Create administrative users
* Seed sample products
* Database maintenance commands
* Technical debugging operations

Benefits:

* Faster development workflow
* Safer operational tasks
* Reduced manual database operations

---

# 📊 Database Monitoring

Production database uses:

## Neon PostgreSQL

Benefits:

* Live database monitoring
* Cloud PostgreSQL infrastructure
* Query visibility
* Easy scaling options
* Developer-friendly database management

---

# 🧪 Testing Strategy

Covered areas:

* Authentication APIs
* Product APIs
* Order creation
* Payment processing
* Webhook handling
* Business logic validation

Testing focus:

* Correctness
* Security
* Transaction consistency
* Failure handling

---

# 🐳 Deployment

Supported:

* Local development
* Docker deployment
* Cloud PostgreSQL deployment

Environment driven configuration:

```
DATABASE_URL=
SECRET_KEY=
JWT_SECRET=
STRIPE_KEY=
BKASH_KEY=
REDIS_URL=
```

---

# 📚 API Documentation

Interactive documentation available through:

```
/docs
```

Powered by FastAPI OpenAPI integration.

---

# 🔮 Future Improvements

## 🤖 AI Fraud Detection

Integrate AI models to analyze:

* Suspicious transactions
* User behavior patterns
* Payment anomalies

---

## 💳 Multiple Payment Gateway Support

Extend payment strategy layer with:

* Additional local gateways
* International payment providers
* Cryptocurrency payments

---

## 🤖 AI Customer Support Chatbot

Future AI assistant capabilities:

* Order tracking
* Product recommendations
* Customer support automation

---

## 🚚 Automated Order Processing

Integration with third-party courier services:

* Automatic shipment creation
* Tracking synchronization
* Delivery status updates

---

## ⚡ Performance Optimization

Planned improvements:

* Advanced database indexing
* Query optimization
* Database profiling
* Connection pooling
* Read replicas

---

## 📨 Event Driven Architecture

Future migration:

```
API Service
      |
      ↓
RabbitMQ
      |
 -----------------
 |       |        |
Order  Payment  Notification
Service Service  Service
```

Benefits:

* Async processing
* Better scalability
* Independent service deployment

---

# 🎯 Engineering Goals

This project focuses on:

✅ Clean architecture
✅ Secure backend development
✅ Scalable database design
✅ Maintainable business logic
✅ Modern Python ecosystem
✅ Production-ready engineering practices

Built with the goal of evolving from a monolithic backend into a scalable distributed commerce platform.
