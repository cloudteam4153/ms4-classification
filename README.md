# University Management API

A FastAPI-based REST API for managing university resources including persons, addresses, books, and courses. This project demonstrates modern Python web development using FastAPI, Pydantic v2, and type hints.

## Features

- **Person Management**: Create, read, update, and delete person records with Columbia UNI support
- **Address Management**: Handle multiple addresses per person with full CRUD operations
- **Book Management**: Manage library books with ISBN, author, publisher, and availability tracking
- **Course Management**: Handle course information including codes, instructors, semesters, and credits
- **Health Monitoring**: Built-in health check endpoints for monitoring
- **Advanced Filtering**: Query endpoints with multiple filter parameters
- **OpenAPI Documentation**: Auto-generated interactive API documentation

## API Endpoints

### Health Check
- `GET /health` - Basic health check
- `GET /health/{path_echo}` - Health check with path parameter

### Persons
- `POST /persons` - Create a new person
- `GET /persons` - List all persons (with filtering)
- `GET /persons/{person_id}` - Get specific person
- `PATCH /persons/{person_id}` - Update person
- `DELETE /persons/{person_id}` - Delete person

### Addresses
- `POST /addresses` - Create a new address
- `GET /addresses` - List all addresses (with filtering)
- `GET /addresses/{address_id}` - Get specific address
- `PATCH /addresses/{address_id}` - Update address
- `DELETE /addresses/{address_id}` - Delete address

### Books
- `POST /books` - Create a new book
- `GET /books` - List all books (with filtering)
- `GET /books/{book_id}` - Get specific book
- `PATCH /books/{book_id}` - Update book
- `DELETE /books/{book_id}` - Delete book

### Courses
- `POST /courses` - Create a new course
- `GET /courses` - List all courses (with filtering)
- `GET /courses/{course_id}` - Get specific course
- `PATCH /courses/{course_id}` - Update course
- `DELETE /courses/{course_id}` - Delete course

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd university-management-api
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the development server:
```bash
python main.py
```

2. The API will be available at `http://localhost:8000`

3. Access the interactive API documentation at:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## Configuration

The API runs on port 8000 by default. You can change this by setting the `FASTAPIPORT` environment variable:

```bash
export FASTAPIPORT=3000
python main.py
```

## Data Models

### Person
- `id`: UUID (auto-generated)
- `uni`: Columbia University Network ID
- `first_name`: First name
- `last_name`: Last name
- `email`: Email address
- `phone`: Phone number
- `birth_date`: Date of birth
- `addresses`: List of associated addresses

### Address
- `id`: UUID
- `street`: Street address
- `city`: City
- `state`: State/Region
- `postal_code`: Postal/ZIP code
- `country`: Country

### Book
- `id`: UUID (auto-generated)
- `isbn`: International Standard Book Number
- `title`: Book title
- `author`: Author name
- `publisher`: Publisher name
- `genre`: Book genre (optional)
- `available`: Availability status

### Course
- `id`: UUID (auto-generated)
- `course_code`: Course identifier (e.g., "CS101")
- `title`: Course title
- `instructor`: Instructor name
- `semester`: Semester (FALL, SPRING, SUMMER)
- `year`: Academic year
- `credits`: Credit hours
- `active`: Course status

## Filtering

Most list endpoints support filtering via query parameters:

- **Persons**: Filter by UNI, name, email, phone, birth date, city, country
- **Addresses**: Filter by street, city, state, postal code, country
- **Books**: Filter by ISBN, title, author, publisher, genre, availability
- **Courses**: Filter by course code, title, instructor, semester, year, credits, active status

Example:
```bash
GET /persons?first_name=John&city=New York
GET /books?author=Smith&available=true
GET /courses?semester=FALL&year=2024
```

## Development

This project uses:
- **FastAPI** for the web framework
- **Pydantic v2** for data validation and serialization
- **Uvicorn** as the ASGI server
- **Python 3.8+** with type hints

## License

This project is part of a cloud computing homework assignment.

## Contributing

This is an academic project. Please refer to the course guidelines for any collaboration policies.
