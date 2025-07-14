# KPA Form Data API

A FastAPI-based REST API for managing KPA (Key Performance Area) form data with PostgreSQL database support.

## 🚀 Features

- **Authentication**: JWT-based authentication system
- **KPA Forms Management**: Create, read, and manage KPA forms
- **Database Integration**: PostgreSQL with asyncpg for async operations
- **Data Validation**: Pydantic models for request/response validation
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Pagination**: Support for paginated responses
- **Filtering**: Filter KPA forms by employee ID and department
- **Security**: Bearer token authentication with JWT

## 📋 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login with phone number and password

### KPA Forms
- `POST /api/v1/kpa/forms` - Create a new KPA form
- `GET /api/v1/kpa/forms` - Get paginated list of KPA forms with filtering
- `GET /api/v1/kpa/forms/{form_id}` - Get specific KPA form by ID

### Health Check
- `GET /` - API health check endpoint

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.104.1
- **Database**: PostgreSQL with asyncpg
- **Authentication**: JWT (PyJWT)
- **Validation**: Pydantic
- **Server**: Uvicorn
- **Environment**: Python 3.8+

## 📦 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- PostgreSQL database
- pip (Python package manager)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd kpa-form-api
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Database Setup
1. Install PostgreSQL and create a database:
```sql
CREATE DATABASE kpa_db;
```

2. Run the database setup script:
```bash
psql -U your_username -d kpa_db -f database_setup.sql
```

### 4. Environment Configuration
1. Copy the `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Update the `.env` file with your database credentials:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/kpa_db
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
```

### 5. Run the Application
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 📖 API Usage

### 1. Authentication
First, login to get a JWT token:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "7760873976",
    "password": "to_share@123"
  }'
```

Response:
```json
{
  "success": true,
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "expires_at": "2025-07-15T14:30:00Z"
}
```

### 2. Create KPA Form
```bash
curl -X POST "http://localhost:8000/api/v1/kpa/forms" \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "EMP004",
    "employee_name": "Alice Johnson",
    "department": "Marketing",
    "designation": "Marketing Manager",
    "performance_period": "Q1-2025",
    "kpa_title": "Brand Awareness Campaign",
    "kpa_description": "Increase brand awareness through digital marketing campaigns",
    "target_value": 75.0,
    "achieved_value": 80.0,
    "weightage": 25.0,
    "remarks": "Excellent performance in digital marketing"
  }'
```

### 3. Get KPA Forms List
```bash
curl -X GET "http://localhost:8000/api/v1/kpa/forms?page=1&limit=10" \
  -H "Authorization: Bearer <your-token>"
```

### 4. Get KPA Form by ID
```bash
curl -X GET "http://localhost:8000/api/v1/kpa/forms/{form_id}" \
  -H "Authorization: Bearer <your-token>"
```

## 🔧 API Documentation

Once the server is running, you can access:
- **Interactive API Documentation**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 📊 Database Schema

### Users Table
- `id`: UUID (Primary Key)
- `phone_number`: VARCHAR(15) (Unique)
- `password_hash`: VARCHAR(255)
- `created_at`: TIMESTAMP
- `updated_at`: TIMESTAMP

### KPA Forms Table
- `id`: UUID (Primary Key)
- `employee_id`: VARCHAR(50)
- `employee_name`: VARCHAR(100)
- `department`: VARCHAR(100)
- `designation`: VARCHAR(100)
- `performance_period`: VARCHAR(50)
- `kpa_title`: VARCHAR(200)
- `kpa_description`: TEXT
- `target_value`: DECIMAL(10,2)
- `achieved_value`: DECIMAL(10,2)
- `weightage`: DECIMAL(5,2)
- `score`: DECIMAL(5,2) (Calculated automatically)
- `remarks`: TEXT
- `created_at`: TIMESTAMP
- `updated_at`: TIMESTAMP
- `created_by`: UUID (Foreign Key to users.id)

## 🧪 Testing

### Using Postman
1. Import the provided Postman collection: `kpa_api_postman_collection.json`
2. Set the base URL to `http://localhost:8000`
3. Use the Login endpoint to get a token
4. The token will be automatically set in the collection variables
5. Test other endpoints using the authenticated token

### Manual Testing
1. Start the server: `python main.py`
2. Visit http://localhost:8000/docs for interactive testing
3. Use the "Authorize" button to set your JWT token
4. Test all endpoints through the Swagger UI

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: SHA-256 hashing for password storage
- **CORS Protection**: Configurable CORS middleware
- **Input Validation**: Pydantic models for request validation
- **SQL Injection Prevention**: Parameterized queries with asyncpg

## 🚧 Limitations & Assumptions

1. **Authentication**: Basic phone number + password authentication (no OTP verification)
2. **File Upload**: Not implemented in current version
3. **User Management**: Only basic user authentication, no registration endpoint
4. **Data Validation**: Basic validation implemented, can be enhanced
5. **Caching**: No caching implemented for database queries
6. **Rate Limiting**: No rate limiting implemented
7. **Logging**: Basic logging, can be enhanced for production

## 🔄 Future Enhancements

- User registration endpoint
- File upload support for KPA documents
- Advanced filtering and search capabilities
- Data export functionality (CSV/Excel)
- Email notifications for KPA submissions
- Role-based access control
- Audit logging for data changes
- Performance optimization with caching

## 📝 Sample Data

The database setup includes sample data:
- Default user: Phone `7760873976`, Password `to_share@123`
- Sample KPA forms for different departments (IT, HR, Sales)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues or questions, please create an issue in the repository or contact the development team.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
