Fix the FastAPI OpenAPI duplicate operation ID warning in the payment webhook routes.

Issue:
FastAPI shows:
"Duplicate Operation ID bkash_callback_api_v1_payments_webhooks_bkash_get"

Current routes:
- GET  /api/v1/payments/webhooks/bkash  -> bkash_callback
- POST /api/v1/payments/webhooks/bkash  -> bkash_callback

Tasks:
1. Find the duplicate bKash webhook route definitions.
2. Rename the endpoint functions clearly.
3. Add explicit unique operation_id values for each route.
4. Keep the API behavior unchanged.
5. Follow production payment webhook naming conventions:
   - GET route should represent redirect/callback handling if needed.
   - POST route should represent the actual webhook receiver.
6. Ensure Swagger/OpenAPI generates without duplicate operation IDs.
7. Run a quick verification after changes.


Review and improve the Category and Product domain models for an ecommerce system.

Context:
The project currently has Category and Product SQLAlchemy models. Category supports hierarchical data using a self-referencing parent_id relationship. Product currently does not have a proper relationship with Category.

Requirements:
1. Add a proper Category ↔ Product relationship inside the same Catalog domain.
2. Keep Category and Product together because they are tightly coupled ecommerce concepts.
3. Add Product.category_id as a foreign key referencing categories.id.
4. Add SQLAlchemy relationships with proper back_populates.
5. Keep the design migration-friendly for future service extraction without premature microservice separation.
6. Preserve clean architecture and avoid over-engineering.
7. Ensure:
   - category hierarchy traversal supports DFS use cases
   - product recommendation can query products by category/subcategories efficiently
   - database indexes are optimized for common ecommerce queries
8. Review existing models and only make necessary changes.
9. Generate/update Alembic migration if schema changes are required.
10. Verify the models are consistent with the existing database schema using Alembic check.

2.2.5 DFS + Caching Requirement
 Use DFS in Product Recommendation / Category Hierarchy to traverse the category tree for recommending related products efficiently, and cache the category tree in Redis/memcached to minimize database calls and speed up repeated traversals.