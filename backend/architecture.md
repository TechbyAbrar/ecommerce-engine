#Layered Clean Architecture (Shift to microservices easily in future)

                    Client
                      │
                      ▼
                FastAPI Routers
                      │
                      ▼
              Dependency Injection
                      │
                      ▼
                Service Layer
                      │
      ┌───────────────┼────────────────┐
      ▼               ▼                ▼
 Auth Service    Order Service    Payment Service
      │               │                │
      ▼               ▼                ▼
 Repository      Repository      Strategy Pattern
      │               │                │
      └───────────────┼────────────────┘
                      ▼
                PostgreSQL
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
        Redis               External APIs
      (Cache/Token)      Stripe / bKash