// =============================================================================
// MongoDB Initialization Script
// =============================================================================
// This script runs when MongoDB container starts for the first time
// =============================================================================

// Switch to the Skycart database
db = db.getSiblingDB('Skycart');

// Create collections with validation
db.createCollection('users', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['name', 'email', 'password', 'role'],
      properties: {
        name: {
          bsonType: 'string',
          description: 'User name is required'
        },
        email: {
          bsonType: 'string',
          pattern: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$',
          description: 'Must be a valid email address'
        },
        password: {
          bsonType: 'string',
          minLength: 6,
          description: 'Password must be at least 6 characters'
        },
        role: {
          enum: ['user', 'admin'],
          description: 'Role must be either user or admin'
        }
      }
    }
  }
});

db.createCollection('products');
db.createCollection('orders');

// Create indexes for users collection
db.users.createIndex({ email: 1 }, { unique: true });
db.users.createIndex({ reset_password_token: 1 });
db.users.createIndex({ created_at: -1 });

// Create indexes for products collection
db.products.createIndex({ name: 1 });
db.products.createIndex({ category: 1 });
db.products.createIndex({ price: 1 });
db.products.createIndex({ ratings: -1 });
db.products.createIndex({ created_at: -1 });
db.products.createIndex(
  { name: 'text', description: 'text' },
  { weights: { name: 10, description: 5 } }
);

// Create indexes for orders collection
db.orders.createIndex({ user: 1 });
db.orders.createIndex({ order_status: 1 });
db.orders.createIndex({ created_at: -1 });
db.orders.createIndex({ 'payment_info.id': 1 });

// Create admin user (password: admin123 - change in production!)
// Password hash for 'admin123' using bcrypt
const adminPasswordHash = '$2b$10$rIJxQq1TQx7gQVYxRsKHSeZPMvqMO0nkIxHmzMRN7/Qj3dqW7pDuy';

db.users.insertOne({
  name: 'Admin User',
  email: 'admin@Skycart.com',
  password: adminPasswordHash,
  role: 'admin',
  avatar: null,
  created_at: new Date()
});

print('='.repeat(60));
print('MongoDB initialized successfully!');
print('Admin user created: admin@Skycart.com');
print('='.repeat(60));
