# JVLCart - Full Stack E-Commerce Application Documentation

> **Purpose**: Learning reference and interview preparation guide
> **Stack**: FastAPI (Python) + React (JavaScript) + MongoDB
> **Version**: 2.0.0

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [FastAPI Backend](#2-fastapi-backend)
   - [Project Structure](#21-project-structure)
   - [Core Configuration](#22-core-configuration)
   - [Authentication & Security](#23-authentication--security)
   - [Domain Layer](#24-domain-layer)
   - [Service Layer](#25-service-layer)
   - [API Endpoints](#26-api-endpoints)
   - [Database & Repository Pattern](#27-database--repository-pattern)
   - [Middleware](#28-middleware)
3. [React Frontend](#3-react-frontend)
   - [Project Structure](#31-project-structure)
   - [State Management (Redux)](#32-state-management-redux)
   - [Components](#33-components)
   - [Routing](#34-routing)
   - [API Integration](#35-api-integration)
4. [Key Concepts for Interviews](#4-key-concepts-for-interviews)
5. [Common Interview Questions](#5-common-interview-questions)

---

# 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT (Browser)                         │
│                    React + Redux + React Router                  │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 │ HTTP/HTTPS (REST API)
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Middleware  │→ │  API Layer  │→ │    Service Layer        │  │
│  │ (Auth,CORS) │  │ (Endpoints) │  │ (Business Logic)        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                                              │                   │
│                                              ▼                   │
│                         ┌─────────────────────────────────────┐  │
│                         │  Domain Layer (Entities, Repos)     │  │
│                         └─────────────────────────────────────┘  │
│                                              │                   │
│                                              ▼                   │
│                         ┌─────────────────────────────────────┐  │
│                         │  Infrastructure (MongoDB Driver)    │  │
│                         └─────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │    MongoDB Database     │
                    │   (Users, Products,     │
                    │    Orders, Reviews)     │
                    └─────────────────────────┘
```

### Design Patterns Used

| Pattern | Where Used | Purpose |
|---------|------------|---------|
| **Clean Architecture** | Backend | Separation of concerns |
| **Repository Pattern** | Backend | Data access abstraction |
| **Dependency Injection** | Backend | Loose coupling |
| **Flux/Redux Pattern** | Frontend | Predictable state management |
| **Container/Component** | Frontend | Separation of logic and UI |

---

# 2. FastAPI Backend

## 2.1 Project Structure

```
fastapi-backend/
├── app/
│   ├── main.py                    # Application entry point
│   ├── core/                      # Core configurations
│   │   ├── config.py              # Environment settings
│   │   ├── security.py            # JWT & password utilities
│   │   ├── dependencies.py        # Database setup
│   │   ├── exceptions.py          # Custom exceptions
│   │   └── logging.py             # Structured logging
│   ├── api/v1/                    # API version 1
│   │   ├── endpoints/             # Route handlers
│   │   │   ├── auth.py            # Authentication routes
│   │   │   ├── users.py           # User management
│   │   │   ├── products.py        # Product CRUD
│   │   │   ├── orders.py          # Order management
│   │   │   └── payments.py        # Stripe payments
│   │   ├── schemas/               # Pydantic models
│   │   └── dependencies.py        # DI configuration
│   ├── domain/                    # Business domain
│   │   ├── users/                 # User entity & repo
│   │   ├── products/              # Product entity & repo
│   │   ├── orders/                # Order entity & repo
│   │   └── shared/                # Base classes
│   ├── services/                  # Business logic
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── product_service.py
│   │   ├── order_service.py
│   │   └── payment_service.py
│   ├── infrastructure/            # Data access
│   │   └── repositories/          # MongoDB implementations
│   └── middleware/                # HTTP middleware
├── tests/                         # Test files
├── Dockerfile                     # Container config
├── docker-compose.yml             # Multi-service setup
└── requirements.txt               # Python dependencies
```

---

## 2.2 Core Configuration

### Config Module (`app/core/config.py`)

**Purpose**: Centralized environment-based configuration using Pydantic Settings

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "SkyCart API"
    ENVIRONMENT: str = "development"  # dev/staging/production
    DEBUG: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "Skycart"

    # JWT Authentication
    JWT_SECRET: str = "your-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 1 day

    # External Services
    STRIPE_SECRET_KEY: str
    STRIPE_PUBLISHABLE_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
```

**Interview Tip**: Pydantic Settings provides automatic environment variable parsing, validation, and type coercion.

---

## 2.3 Authentication & Security

### Security Module (`app/core/security.py`)

**JWT Token Flow:**
```
1. User Login → Credentials Verified → JWT Token Generated
2. Client stores token → Sends in Authorization header
3. Backend decodes token → Validates → Extracts user info
```

**Key Functions:**

```python
# Password Hashing (Argon2)
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# JWT Token Creation
def create_access_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,      # Subject (user identifier)
        "role": role,        # User role for authorization
        "exp": datetime.utcnow() + timedelta(days=1),  # Expiration
        "iat": datetime.utcnow(),  # Issued at
        "type": "access"
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

# Token Decoding
def decode_token(token: str) -> TokenPayload:
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    return TokenPayload(**payload)
```

**Token Payload Structure:**
```python
class TokenPayload:
    user_id: str    # User's database ID
    role: str       # "user" or "admin"
    exp: datetime   # Expiration timestamp
    iat: datetime   # Issued at timestamp
    type: str       # "access" or "refresh"
```

---

## 2.4 Domain Layer

### Entity Pattern

**Base Entity** (`app/domain/shared/entity.py`):
```python
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class BaseEntity:
    id: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
```

**User Entity** (`app/domain/users/entities.py`):
```python
@dataclass
class User(BaseEntity):
    name: str = ""
    email: str = ""
    password: str = ""           # Hashed
    avatar: str = ""
    role: UserRole = UserRole.USER
    reset_password_token: str | None = None
    reset_password_token_expire: datetime | None = None

    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    def to_public_dict(self) -> dict:
        """Returns user data without sensitive fields"""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "avatar": self.avatar,
            "role": self.role.value
        }
```

**Product Entity** (`app/domain/products/entities.py`):
```python
@dataclass
class Product(BaseEntity):
    name: str = ""
    price: Decimal = Decimal("0")
    description: str = ""
    ratings: float = 0.0           # Average rating (0-5)
    images: list[ProductImage] = field(default_factory=list)
    category: ProductCategory = ProductCategory.ELECTRONICS
    seller: str = ""
    stock: int = 0
    num_of_reviews: int = 0
    reviews: list[ProductReview] = field(default_factory=list)
    user: str = ""                 # Seller's user ID

@dataclass
class ProductReview:
    user: str           # Reviewer's user ID
    rating: float       # 0-5
    comment: str
```

**Order Entity** (`app/domain/orders/entities.py`):
```python
@dataclass
class Order(BaseEntity):
    user: str                              # Buyer's user ID
    shipping_info: ShippingInfo
    order_items: list[OrderItem]
    items_price: Decimal
    tax_price: Decimal
    shipping_price: Decimal
    total_price: Decimal
    payment_info: PaymentInfo
    paid_at: datetime | None = None
    delivered_at: datetime | None = None
    order_status: OrderStatus = OrderStatus.PENDING

@dataclass
class OrderItem:
    product: str        # Product ID
    name: str
    price: Decimal
    quantity: int
    image: str

    @property
    def subtotal(self) -> Decimal:
        return self.price * self.quantity
```

### Value Objects (Enums)

```python
# User roles
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

# Product categories
class ProductCategory(str, Enum):
    ELECTRONICS = "Electronics"
    MOBILE_PHONES = "Mobile Phones"
    LAPTOPS = "Laptops"
    ACCESSORIES = "Accessories"
    # ... 12 total categories

# Order status
class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
```

---

## 2.5 Service Layer

### Service Pattern

Services contain **business logic** and orchestrate repositories:

**AuthService** (`app/services/auth_service.py`):
```python
class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def register(self, name: str, email: str, password: str, avatar: str = "") -> tuple[User, str]:
        # Check if email exists
        existing = await self.user_repository.get_by_email(email)
        if existing:
            raise UserAlreadyExistsError(email)

        # Create user with hashed password
        user = User(
            name=name,
            email=email,
            password=hash_password(password),
            avatar=avatar
        )
        created_user = await self.user_repository.create(user)

        # Generate JWT token
        token = create_access_token(created_user.id, created_user.role.value)
        return created_user, token

    async def login(self, email: str, password: str) -> tuple[User, str]:
        user = await self.user_repository.get_by_email(email)
        if not user or not verify_password(password, user.password):
            raise InvalidCredentialsError()

        token = create_access_token(user.id, user.role.value)
        return user, token
```

**ProductService** (`app/services/product_service.py`):
```python
class ProductService:
    async def get_products(
        self,
        keyword: str | None = None,
        category: str | None = None,
        price_min: float | None = None,
        price_max: float | None = None,
        rating_min: float | None = None,
        page: int = 1,
        limit: int = 10
    ) -> tuple[list[Product], int]:
        """Fetch products with filters and pagination"""
        filters = {}

        if keyword:
            filters["$text"] = {"$search": keyword}
        if category:
            filters["category"] = category
        if price_min or price_max:
            filters["price"] = {}
            if price_min: filters["price"]["$gte"] = price_min
            if price_max: filters["price"]["$lte"] = price_max
        if rating_min:
            filters["ratings"] = {"$gte": rating_min}

        skip = (page - 1) * limit
        products = await self.product_repository.filter(filters, skip, limit)
        total = await self.product_repository.count(filters)

        return products, total

    async def add_review(self, product_id: str, user_id: str, rating: float, comment: str) -> Product:
        product = await self.product_repository.get_by_id(product_id)
        if not product:
            raise ProductNotFoundError(product_id)

        # Check if user already reviewed
        existing_review = next((r for r in product.reviews if r.user == user_id), None)
        if existing_review:
            raise ReviewAlreadyExistsError()

        # Add review and recalculate average
        new_review = ProductReview(user=user_id, rating=rating, comment=comment)
        product.reviews.append(new_review)
        product.num_of_reviews = len(product.reviews)
        product.ratings = sum(r.rating for r in product.reviews) / product.num_of_reviews

        return await self.product_repository.update(product)
```

**OrderService** (`app/services/order_service.py`):
```python
class OrderService:
    async def create_order(self, user_id: str, order_data: dict) -> Order:
        # Validate stock for all items
        for item in order_data["order_items"]:
            product = await self.product_repository.get_by_id(item["product"])
            if product.stock < item["quantity"]:
                raise InsufficientStockError(product.name, product.stock)

        # Reduce stock
        for item in order_data["order_items"]:
            await self.product_repository.reduce_stock(item["product"], item["quantity"])

        # Create order
        order = Order(
            user=user_id,
            shipping_info=ShippingInfo(**order_data["shipping_info"]),
            order_items=[OrderItem(**i) for i in order_data["order_items"]],
            items_price=order_data["items_price"],
            tax_price=order_data["tax_price"],
            shipping_price=order_data["shipping_price"],
            total_price=order_data["total_price"],
            payment_info=PaymentInfo(**order_data["payment_info"]),
            paid_at=datetime.utcnow()
        )

        return await self.order_repository.create(order)
```

---

## 2.6 API Endpoints

### Endpoint Structure

**Auth Endpoints** (`app/api/v1/endpoints/auth.py`):

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/register` | User registration | No |
| POST | `/api/v1/auth/login` | User login | No |
| GET | `/api/v1/auth/me` | Get current user | Yes |
| POST | `/api/v1/auth/password/forgot` | Request password reset | No |
| PUT | `/api/v1/auth/password/reset/{token}` | Reset password | No |
| PUT | `/api/v1/auth/password/update` | Change password | Yes |

```python
@router.post("/register", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    auth_service: AuthServiceDep
):
    user, token = await auth_service.register(
        name=request.name,
        email=request.email,
        password=request.password,
        avatar=request.avatar
    )
    return TokenResponse(
        success=True,
        token=token,
        user=user.to_public_dict()
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: CurrentUser):
    """Protected endpoint - requires valid JWT"""
    return UserResponse(**current_user.to_public_dict())
```

**Product Endpoints** (`app/api/v1/endpoints/products.py`):

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/products` | List products (with filters) | No |
| GET | `/api/v1/products/{id}` | Get product details | No |
| POST | `/api/v1/products/admin/product/new` | Create product | Admin |
| PUT | `/api/v1/products/admin/product/{id}` | Update product | Admin |
| DELETE | `/api/v1/products/admin/product/{id}` | Delete product | Admin |
| POST | `/api/v1/products/{id}/review` | Add review | User |

**Query Parameters for Product Listing:**
```
GET /api/v1/products?keyword=phone&category=Electronics&price[gte]=100&price[lte]=1000&ratings[gte]=4&page=1&resPerPage=10
```

**Order Endpoints** (`app/api/v1/endpoints/orders.py`):

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/orders/new` | Create order | User |
| GET | `/api/v1/orders/me` | Get user's orders | User |
| GET | `/api/v1/orders/{id}` | Get order details | User |
| GET | `/api/v1/orders/admin/orders` | All orders | Admin |
| PUT | `/api/v1/orders/{id}/status` | Update order status | Admin |

---

## 2.7 Database & Repository Pattern

### Repository Interface

```python
# Base interface (app/domain/shared/repository.py)
class BaseRepository(ABC, Generic[T]):
    @abstractmethod
    async def create(self, entity: T) -> T: ...

    @abstractmethod
    async def get_by_id(self, id: str) -> T | None: ...

    @abstractmethod
    async def update(self, entity: T) -> T: ...

    @abstractmethod
    async def delete(self, id: str) -> bool: ...

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 10) -> list[T]: ...
```

### MongoDB Implementation

```python
# Base MongoDB repository (app/infrastructure/repositories/base_mongo_repository.py)
class BaseMongoRepository(Generic[T]):
    def __init__(self, database, collection_name: str, entity_class: type[T]):
        self.collection = database[collection_name]
        self.entity_class = entity_class

    async def create(self, entity: T) -> T:
        data = asdict(entity)
        data.pop("id", None)
        result = await self.collection.insert_one(data)
        entity.id = str(result.inserted_id)
        return entity

    async def get_by_id(self, id: str) -> T | None:
        doc = await self.collection.find_one({"_id": ObjectId(id)})
        if not doc:
            return None
        doc["id"] = str(doc.pop("_id"))
        return self.entity_class(**doc)

    async def filter(self, filters: dict, skip: int = 0, limit: int = 10) -> list[T]:
        cursor = self.collection.find(filters).skip(skip).limit(limit)
        entities = []
        async for doc in cursor:
            doc["id"] = str(doc.pop("_id"))
            entities.append(self.entity_class(**doc))
        return entities
```

### Database Indexes

```python
# Created on startup (app/core/dependencies.py)
async def init_database():
    db = get_database()

    # Users collection
    await db.users.create_index("email", unique=True)
    await db.users.create_index("reset_password_token")

    # Products collection
    await db.products.create_index("category")
    await db.products.create_index("price")
    await db.products.create_index("ratings")
    await db.products.create_index([("name", "text"), ("description", "text")])  # Text search

    # Orders collection
    await db.orders.create_index("user")
    await db.orders.create_index("order_status")
    await db.orders.create_index("created_at")
```

---

## 2.8 Middleware

### Error Handler (`app/middleware/error_handler.py`)

```python
async def app_exception_handler(request: Request, exc: AppException):
    """Handles all custom application exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.message,
            "error_code": exc.error_code,
            "details": exc.details
        }
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """Catches unhandled exceptions"""
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error" if settings.is_production else str(exc),
            "error_code": "INTERNAL_ERROR"
        }
    )
```

### Correlation ID Middleware (`app/middleware/correlation_id.py`)

**Purpose**: Distributed tracing across microservices

```python
class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

        # Bind to logging context
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        return response
```

### Logging Middleware (`app/middleware/logging_middleware.py`)

```python
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")

        response = await call_next(request)

        # Log response with timing
        process_time = (time.time() - start_time) * 1000
        logger.info(f"Response: {response.status_code} ({process_time:.2f}ms)")

        response.headers["X-Process-Time"] = str(process_time)
        return response
```

---

# 3. React Frontend

## 3.1 Project Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── App.js                     # Main app with routing
│   ├── index.js                   # Entry point
│   ├── store.js                   # Redux store configuration
│   ├── slices/                    # Redux slices
│   │   ├── authSlice.js           # Authentication state
│   │   ├── productsSlice.js       # Products list state
│   │   ├── productSlice.js        # Single product state
│   │   ├── cartSlice.js           # Shopping cart state
│   │   ├── orderSlice.js          # Orders state
│   │   └── userSlice.js           # Admin user management
│   ├── actions/                   # Async action creators
│   │   ├── userActions.js         # Auth & user actions
│   │   ├── productActions.js      # Product actions
│   │   ├── cartActions.js         # Cart actions
│   │   └── orderActions.js        # Order actions
│   └── components/
│       ├── layouts/               # Header, Footer, etc.
│       ├── product/               # Product components
│       ├── user/                  # Auth components
│       ├── cart/                  # Cart & checkout
│       ├── order/                 # Order components
│       ├── admin/                 # Admin dashboard
│       └── route/                 # Route protection
└── package.json
```

---

## 3.2 State Management (Redux)

### Store Configuration (`src/store.js`)

```javascript
import { configureStore } from '@reduxjs/toolkit';
import productsReducer from './slices/productsSlice';
import productReducer from './slices/productSlice';
import authReducer from './slices/authSlice';
import cartReducer from './slices/cartSlice';
import orderReducer from './slices/orderSlice';
import userReducer from './slices/userSlice';

const store = configureStore({
    reducer: {
        productsState: productsReducer,   // Products list
        productState: productReducer,     // Single product + reviews
        authState: authReducer,           // Authentication
        cartState: cartReducer,           // Shopping cart
        orderState: orderReducer,         // Orders
        userState: userReducer            // Admin user management
    },
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware({ serializableCheck: false })
});

export default store;
```

### Redux Slice Pattern

**Auth Slice** (`src/slices/authSlice.js`):

```javascript
import { createSlice } from '@reduxjs/toolkit';

const authSlice = createSlice({
    name: 'auth',
    initialState: {
        loading: false,
        isAuthenticated: false,
        user: null,
        error: null,
        isUpdated: false,
        message: null
    },
    reducers: {
        // Login actions
        loginRequest(state) {
            state.loading = true;
        },
        loginSuccess(state, action) {
            state.loading = false;
            state.isAuthenticated = true;
            state.user = action.payload.user;
        },
        loginFail(state, action) {
            state.loading = false;
            state.error = action.payload;
        },

        // Load user (on app mount)
        loadUserRequest(state) {
            state.loading = true;
        },
        loadUserSuccess(state, action) {
            state.loading = false;
            state.isAuthenticated = true;
            state.user = action.payload.user;
        },
        loadUserFail(state, action) {
            state.loading = false;
            state.isAuthenticated = false;
        },

        // Logout
        logoutSuccess(state) {
            state.isAuthenticated = false;
            state.user = null;
        },

        // Clear errors
        clearError(state) {
            state.error = null;
        }
    }
});

export const {
    loginRequest, loginSuccess, loginFail,
    loadUserRequest, loadUserSuccess, loadUserFail,
    logoutSuccess, clearError
} = authSlice.actions;

export default authSlice.reducer;
```

**Cart Slice with localStorage** (`src/slices/cartSlice.js`):

```javascript
const cartSlice = createSlice({
    name: 'cart',
    initialState: {
        items: localStorage.getItem('cartItems')
            ? JSON.parse(localStorage.getItem('cartItems'))
            : [],
        loading: false,
        shippingInfo: localStorage.getItem('shippingInfo')
            ? JSON.parse(localStorage.getItem('shippingInfo'))
            : {}
    },
    reducers: {
        addCartItemSuccess(state, action) {
            const item = action.payload;
            const existingItem = state.items.find(i => i.product === item.product);

            if (existingItem) {
                state.items = state.items.map(i =>
                    i.product === item.product ? item : i
                );
            } else {
                state.items.push(item);
            }

            // Persist to localStorage
            localStorage.setItem('cartItems', JSON.stringify(state.items));
        },

        removeItemFromCart(state, action) {
            state.items = state.items.filter(i => i.product !== action.payload);
            localStorage.setItem('cartItems', JSON.stringify(state.items));
        },

        saveShippingInfo(state, action) {
            state.shippingInfo = action.payload;
            localStorage.setItem('shippingInfo', JSON.stringify(action.payload));
        },

        orderCompleted(state) {
            state.items = [];
            localStorage.removeItem('cartItems');
            sessionStorage.removeItem('orderInfo');
        }
    }
});
```

### Async Actions (Thunks)

**User Actions** (`src/actions/userActions.js`):

```javascript
import axios from 'axios';
import {
    loginRequest, loginSuccess, loginFail,
    registerRequest, registerSuccess, registerFail,
    loadUserRequest, loadUserSuccess, loadUserFail
} from '../slices/authSlice';

// Login action
export const login = (email, password) => async (dispatch) => {
    try {
        dispatch(loginRequest());

        const { data } = await axios.post('/api/v1/login', { email, password });

        dispatch(loginSuccess(data));
    } catch (error) {
        dispatch(loginFail(error.response.data.message));
    }
};

// Register action (with file upload)
export const register = (userData) => async (dispatch) => {
    try {
        dispatch(registerRequest());

        const config = {
            headers: { 'Content-Type': 'multipart/form-data' }
        };

        const { data } = await axios.post('/api/v1/register', userData, config);

        dispatch(registerSuccess(data));
    } catch (error) {
        dispatch(registerFail(error.response.data.message));
    }
};

// Load user on app mount
export const loadUser = () => async (dispatch) => {
    try {
        dispatch(loadUserRequest());

        const { data } = await axios.get('/api/v1/myprofile');

        dispatch(loadUserSuccess(data));
    } catch (error) {
        dispatch(loadUserFail(error.response.data.message));
    }
};
```

**Product Actions** (`src/actions/productActions.js`):

```javascript
export const getProducts = (keyword, price, category, rating, currentPage) => async (dispatch) => {
    try {
        dispatch(productsRequest());

        let link = `/api/v1/products?page=${currentPage}`;

        if (keyword) link += `&keyword=${keyword}`;
        if (price) link += `&price[gte]=${price[0]}&price[lte]=${price[1]}`;
        if (category) link += `&category=${category}`;
        if (rating) link += `&ratings[gte]=${rating}`;

        const { data } = await axios.get(link);

        dispatch(productsSuccess(data));
    } catch (error) {
        dispatch(productsFail(error.response.data.message));
    }
};
```

---

## 3.3 Components

### Layout Components

**Header** (`src/components/layouts/Header.js`):
```jsx
const Header = () => {
    const { isAuthenticated, user } = useSelector(state => state.authState);
    const { items: cartItems } = useSelector(state => state.cartState);
    const dispatch = useDispatch();

    const logoutHandler = () => {
        dispatch(logout());
    };

    return (
        <Navbar>
            <Navbar.Brand><Link to="/">JVLCart</Link></Navbar.Brand>

            <Search />

            <Nav>
                <Link to="/cart">
                    Cart <span className="badge">{cartItems.length}</span>
                </Link>

                {isAuthenticated ? (
                    <Dropdown>
                        <Dropdown.Toggle>{user.name}</Dropdown.Toggle>
                        <Dropdown.Menu>
                            {user.role === 'admin' && (
                                <Link to="/admin/dashboard">Dashboard</Link>
                            )}
                            <Link to="/orders">Orders</Link>
                            <Link to="/myprofile">Profile</Link>
                            <Dropdown.Item onClick={logoutHandler}>Logout</Dropdown.Item>
                        </Dropdown.Menu>
                    </Dropdown>
                ) : (
                    <Link to="/login">Login</Link>
                )}
            </Nav>
        </Navbar>
    );
};
```

### Product Components

**Product Card** (`src/components/product/Product.js`):
```jsx
const Product = ({ product }) => {
    return (
        <Card>
            <Link to={`/product/${product._id}`}>
                <Card.Img src={product.images[0].image} />
            </Link>
            <Card.Body>
                <Card.Title>
                    <Link to={`/product/${product._id}`}>{product.name}</Link>
                </Card.Title>
                <div className="ratings">
                    <Rating value={product.ratings} />
                    <span>({product.numOfReviews} reviews)</span>
                </div>
                <Card.Text className="price">${product.price}</Card.Text>
                <Link to={`/product/${product._id}`} className="btn">
                    View Details
                </Link>
            </Card.Body>
        </Card>
    );
};
```

**Product Detail** (`src/components/product/ProductDetail.js`):
```jsx
const ProductDetail = () => {
    const { id } = useParams();
    const dispatch = useDispatch();
    const { product, loading, error } = useSelector(state => state.productState);
    const { isAuthenticated } = useSelector(state => state.authState);
    const [quantity, setQuantity] = useState(1);

    useEffect(() => {
        dispatch(getProduct(id));
    }, [dispatch, id]);

    const addToCart = () => {
        dispatch(addCartItem(product._id, quantity));
        toast.success('Item added to cart');
    };

    const submitReview = (reviewData) => {
        dispatch(createReview({ productId: id, ...reviewData }));
    };

    return (
        <div>
            <Row>
                <Col md={6}>
                    <Carousel>
                        {product.images.map((img, i) => (
                            <Carousel.Item key={i}>
                                <img src={img.image} alt={product.name} />
                            </Carousel.Item>
                        ))}
                    </Carousel>
                </Col>
                <Col md={6}>
                    <h3>{product.name}</h3>
                    <p>Product # {product._id}</p>
                    <Rating value={product.ratings} />
                    <p className="price">${product.price}</p>
                    <p className={product.stock > 0 ? 'in-stock' : 'out-of-stock'}>
                        {product.stock > 0 ? 'In Stock' : 'Out of Stock'}
                    </p>

                    <div className="quantity-selector">
                        <button onClick={() => setQuantity(Math.max(1, quantity - 1))}>-</button>
                        <span>{quantity}</span>
                        <button onClick={() => setQuantity(Math.min(product.stock, quantity + 1))}>+</button>
                    </div>

                    <button
                        onClick={addToCart}
                        disabled={product.stock === 0}
                    >
                        Add to Cart
                    </button>

                    {isAuthenticated && <ReviewModal onSubmit={submitReview} />}
                </Col>
            </Row>

            <h4>Reviews</h4>
            {product.reviews.map(review => (
                <ProductReview key={review._id} review={review} />
            ))}
        </div>
    );
};
```

### Cart & Checkout Components

**Cart** (`src/components/cart/Cart.js`):
```jsx
const Cart = () => {
    const { items } = useSelector(state => state.cartState);
    const dispatch = useDispatch();

    const increaseQty = (id, qty, stock) => {
        if (qty >= stock) return;
        dispatch(increaseCartItemQty(id));
    };

    const decreaseQty = (id, qty) => {
        if (qty <= 1) return;
        dispatch(decreaseCartItemQty(id));
    };

    const removeItem = (id) => {
        dispatch(removeItemFromCart(id));
    };

    const subtotal = items.reduce((acc, item) => acc + item.price * item.quantity, 0);

    return (
        <div>
            <h2>Your Cart ({items.length} items)</h2>

            {items.map(item => (
                <Row key={item.product}>
                    <Col><img src={item.image} alt={item.name} /></Col>
                    <Col><Link to={`/product/${item.product}`}>{item.name}</Link></Col>
                    <Col>${item.price}</Col>
                    <Col>
                        <button onClick={() => decreaseQty(item.product, item.quantity)}>-</button>
                        <span>{item.quantity}</span>
                        <button onClick={() => increaseQty(item.product, item.quantity, item.stock)}>+</button>
                    </Col>
                    <Col><button onClick={() => removeItem(item.product)}>Remove</button></Col>
                </Row>
            ))}

            <div className="order-summary">
                <p>Subtotal: ${subtotal.toFixed(2)}</p>
                <Link to="/shipping" className="btn">Checkout</Link>
            </div>
        </div>
    );
};
```

**Payment (Stripe)** (`src/components/cart/Payment.js`):
```jsx
import { CardNumberElement, CardExpiryElement, CardCvcElement, useStripe, useElements } from '@stripe/react-stripe-js';

const Payment = () => {
    const stripe = useStripe();
    const elements = useElements();
    const dispatch = useDispatch();
    const navigate = useNavigate();

    const { user } = useSelector(state => state.authState);
    const { items: cartItems, shippingInfo } = useSelector(state => state.cartState);

    const orderInfo = JSON.parse(sessionStorage.getItem('orderInfo'));

    const submitHandler = async (e) => {
        e.preventDefault();

        const paymentData = {
            amount: Math.round(orderInfo.totalPrice * 100)  // Stripe expects cents
        };

        try {
            // Create payment intent
            const { data } = await axios.post('/api/v1/payment/process', paymentData);

            // Confirm payment
            const result = await stripe.confirmCardPayment(data.client_secret, {
                payment_method: {
                    card: elements.getElement(CardNumberElement),
                    billing_details: {
                        name: user.name,
                        email: user.email
                    }
                }
            });

            if (result.error) {
                toast.error(result.error.message);
            } else {
                if (result.paymentIntent.status === 'succeeded') {
                    // Create order
                    const order = {
                        orderItems: cartItems,
                        shippingInfo,
                        itemsPrice: orderInfo.itemsPrice,
                        taxPrice: orderInfo.taxPrice,
                        shippingPrice: orderInfo.shippingPrice,
                        totalPrice: orderInfo.totalPrice,
                        paymentInfo: {
                            id: result.paymentIntent.id,
                            status: result.paymentIntent.status
                        }
                    };

                    dispatch(createOrder(order));
                    dispatch(orderCompleted());
                    navigate('/order/success');
                }
            }
        } catch (error) {
            toast.error(error.response.data.message);
        }
    };

    return (
        <form onSubmit={submitHandler}>
            <div className="form-group">
                <label>Card Number</label>
                <CardNumberElement />
            </div>
            <div className="form-group">
                <label>Card Expiry</label>
                <CardExpiryElement />
            </div>
            <div className="form-group">
                <label>CVC</label>
                <CardCvcElement />
            </div>
            <button type="submit">Pay ${orderInfo?.totalPrice}</button>
        </form>
    );
};
```

### Route Protection

**ProtectedRoute** (`src/components/route/ProtectedRoute.js`):
```jsx
const ProtectedRoute = ({ children, isAdmin = false }) => {
    const { isAuthenticated, loading, user } = useSelector(state => state.authState);

    if (loading) {
        return <Loader />;
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" />;
    }

    if (isAdmin && user.role !== 'admin') {
        return <Navigate to="/" />;
    }

    return children;
};

// Usage in App.js
<Route
    path="/admin/dashboard"
    element={
        <ProtectedRoute isAdmin={true}>
            <Dashboard />
        </ProtectedRoute>
    }
/>
```

---

## 3.4 Routing

### Route Configuration (`src/App.js`)

```jsx
function App() {
    const dispatch = useDispatch();

    useEffect(() => {
        dispatch(loadUser());  // Load user on app mount
    }, [dispatch]);

    return (
        <Router>
            <Header />
            <ToastContainer />

            <Routes>
                {/* Public Routes */}
                <Route path="/" element={<Home />} />
                <Route path="/search/:keyword" element={<ProductSearch />} />
                <Route path="/product/:id" element={<ProductDetail />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/password/forgot" element={<ForgotPassword />} />
                <Route path="/password/reset/:token" element={<ResetPassword />} />
                <Route path="/cart" element={<Cart />} />

                {/* Protected User Routes */}
                <Route path="/myprofile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
                <Route path="/myprofile/update" element={<ProtectedRoute><UpdateProfile /></ProtectedRoute>} />
                <Route path="/shipping" element={<ProtectedRoute><Shipping /></ProtectedRoute>} />
                <Route path="/order/confirm" element={<ProtectedRoute><ConfirmOrder /></ProtectedRoute>} />
                <Route path="/payment" element={<ProtectedRoute><Payment /></ProtectedRoute>} />
                <Route path="/orders" element={<ProtectedRoute><UserOrders /></ProtectedRoute>} />
                <Route path="/order/:id" element={<ProtectedRoute><OrderDetail /></ProtectedRoute>} />

                {/* Admin Routes */}
                <Route path="/admin/dashboard" element={<ProtectedRoute isAdmin><Dashboard /></ProtectedRoute>} />
                <Route path="/admin/products" element={<ProtectedRoute isAdmin><ProductList /></ProtectedRoute>} />
                <Route path="/admin/products/create" element={<ProtectedRoute isAdmin><NewProduct /></ProtectedRoute>} />
                <Route path="/admin/product/:id" element={<ProtectedRoute isAdmin><UpdateProduct /></ProtectedRoute>} />
                <Route path="/admin/orders" element={<ProtectedRoute isAdmin><OrderList /></ProtectedRoute>} />
                <Route path="/admin/order/:id" element={<ProtectedRoute isAdmin><UpdateOrder /></ProtectedRoute>} />
                <Route path="/admin/users" element={<ProtectedRoute isAdmin><UserList /></ProtectedRoute>} />
                <Route path="/admin/user/:id" element={<ProtectedRoute isAdmin><UpdateUser /></ProtectedRoute>} />
            </Routes>

            <Footer />
        </Router>
    );
}
```

---

## 3.5 API Integration

### Axios Configuration

```javascript
// API calls use relative URLs, proxied to backend
// package.json: "proxy": "http://127.0.0.1:8000"

// Standard GET request
const { data } = await axios.get('/api/v1/products');

// POST with JSON
const { data } = await axios.post('/api/v1/login', { email, password });

// POST with FormData (file upload)
const formData = new FormData();
formData.append('name', name);
formData.append('avatar', avatarFile);

const config = { headers: { 'Content-Type': 'multipart/form-data' } };
const { data } = await axios.post('/api/v1/register', formData, config);
```

### Error Handling Pattern

```javascript
export const login = (email, password) => async (dispatch) => {
    try {
        dispatch(loginRequest());
        const { data } = await axios.post('/api/v1/login', { email, password });
        dispatch(loginSuccess(data));
    } catch (error) {
        // Extract error message from backend response
        dispatch(loginFail(error.response?.data?.message || 'Something went wrong'));
    }
};

// In components
useEffect(() => {
    if (error) {
        toast.error(error);          // Show error notification
        dispatch(clearAuthError());   // Clear error from state
    }
}, [error, dispatch]);
```

---

# 4. Key Concepts for Interviews

## Backend Concepts

### 1. Clean Architecture
```
┌──────────────────────────────────────────────┐
│  API Layer (Endpoints, Schemas)              │
│  - HTTP request handling                     │
│  - Request/Response validation               │
├──────────────────────────────────────────────┤
│  Service Layer (Business Logic)              │
│  - Application use cases                     │
│  - Orchestrates domain and infrastructure    │
├──────────────────────────────────────────────┤
│  Domain Layer (Entities, Value Objects)      │
│  - Core business rules                       │
│  - Framework-independent                     │
├──────────────────────────────────────────────┤
│  Infrastructure Layer (Repositories, DB)     │
│  - Data persistence                          │
│  - External service integration              │
└──────────────────────────────────────────────┘
```

### 2. Dependency Injection with FastAPI

```python
# Define dependency
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: UserRepository = Depends(get_user_repository)
) -> User:
    payload = decode_token(token)
    user = await user_repo.get_by_id(payload.user_id)
    if not user:
        raise InvalidTokenError()
    return user

# Type alias for cleaner code
CurrentUser = Annotated[User, Depends(get_current_user)]

# Use in endpoint
@router.get("/profile")
async def get_profile(current_user: CurrentUser):
    return current_user.to_public_dict()
```

### 3. JWT Authentication Flow
```
1. Registration/Login → Generate JWT with user_id and role
2. Client stores JWT → Sends in Authorization: Bearer {token}
3. Backend middleware → Decode JWT → Validate expiration
4. Extract user from DB → Inject into route handler
5. Logout → Client removes token (stateless)
```

### 4. Repository Pattern Benefits
- **Abstraction**: Service layer doesn't know about MongoDB
- **Testability**: Easy to mock repositories in tests
- **Flexibility**: Can swap databases without changing business logic

## Frontend Concepts

### 1. Redux Data Flow
```
User Action → dispatch(action) → Reducer updates state →
Components re-render via useSelector
```

### 2. Redux Toolkit Benefits
- **createSlice**: Reduces boilerplate (actions + reducers in one)
- **Immer**: Write "mutating" logic that produces immutable updates
- **configureStore**: Pre-configured with good defaults

### 3. Protected Routes Pattern
```jsx
// Check authentication and role before rendering
if (!isAuthenticated) return <Navigate to="/login" />;
if (isAdmin && user.role !== 'admin') return <Navigate to="/" />;
return children;
```

### 4. Optimistic UI Updates
- Update local state immediately (e.g., add to cart)
- Persist to localStorage for offline support
- Sync with server in background

---

# 5. Common Interview Questions

## Backend Questions

**Q: How does JWT authentication work?**
> JWT (JSON Web Token) is a stateless authentication mechanism. On login, the server creates a signed token containing user ID and role. The client sends this token in the Authorization header. The server validates the signature and extracts user info without database lookup. Tokens have expiration times for security.

**Q: Explain the Repository Pattern.**
> Repository pattern abstracts data access logic behind an interface. Services call repository methods like `get_by_id()` or `create()` without knowing the underlying database. This allows swapping databases (MongoDB to PostgreSQL) without changing business logic, and makes unit testing easier with mock repositories.

**Q: What is Clean Architecture?**
> Clean Architecture separates concerns into layers: API (HTTP handling), Services (business logic), Domain (entities and rules), Infrastructure (database, external services). Inner layers don't depend on outer layers. The domain layer is framework-independent, making the core business logic testable and portable.

**Q: How do you handle errors in FastAPI?**
> Custom exception classes extend a base `AppException` with status code and error code. Exception handlers catch these and return standardized JSON responses. Unhandled exceptions return generic 500 errors in production (hiding internal details) but full stack traces in development.

**Q: Explain async/await in Python.**
> `async` defines a coroutine that can be paused. `await` pauses execution until an I/O operation completes, allowing other coroutines to run. This enables non-blocking I/O - while waiting for database or HTTP responses, the server can handle other requests, improving throughput.

## Frontend Questions

**Q: How does Redux work?**
> Redux is a predictable state container. State is stored in a single store. Components dispatch actions (objects describing what happened). Reducers are pure functions that take current state and action, returning new state. Components subscribe to state via `useSelector` and re-render when relevant state changes.

**Q: What is Redux Toolkit?**
> Redux Toolkit is the official, opinionated toolset for Redux. `createSlice` combines action creators and reducers. It uses Immer internally, allowing "mutating" syntax that produces immutable updates. `configureStore` sets up the store with good defaults including Redux DevTools.

**Q: How do you protect routes in React?**
> Create a ProtectedRoute component that checks authentication state from Redux. If not authenticated, redirect to login. For admin routes, also check user role. Wrap protected routes with this component. Show a loader while checking auth state to prevent flash of unauthorized content.

**Q: Explain useEffect dependencies.**
> The dependency array controls when useEffect runs. Empty array `[]` runs once on mount. `[id]` runs when `id` changes. No array runs on every render. Missing dependencies cause stale closures (using old values). Include all values from component scope that the effect uses.

**Q: How do you handle API errors in React?**
> In async actions, catch errors and dispatch failure actions with error messages. Store error in Redux state. In components, use useEffect to watch for errors, show toast notifications, then dispatch action to clear error. This centralizes error handling and ensures errors are displayed consistently.

---

## Quick Reference: API Endpoints

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/register` | POST | Register user |
| `/api/v1/auth/login` | POST | Login |
| `/api/v1/auth/me` | GET | Current user |
| `/api/v1/auth/password/forgot` | POST | Request reset |
| `/api/v1/auth/password/reset/:token` | PUT | Reset password |

### Products
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/products` | GET | List (with filters) |
| `/api/v1/products/:id` | GET | Get one |
| `/api/v1/products/:id/review` | POST | Add review |
| `/api/v1/admin/products` | GET | Admin list |
| `/api/v1/admin/product/new` | POST | Create |
| `/api/v1/admin/product/:id` | PUT/DELETE | Update/Delete |

### Orders
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/orders/new` | POST | Create order |
| `/api/v1/orders/me` | GET | User's orders |
| `/api/v1/orders/:id` | GET | Order details |
| `/api/v1/admin/orders` | GET | All orders |
| `/api/v1/admin/order/:id` | PUT | Update status |

### Payments
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/payment/process` | POST | Create PaymentIntent |
| `/api/v1/payment/stripeapi` | GET | Get publishable key |

---

*Documentation generated for learning and interview preparation.*
