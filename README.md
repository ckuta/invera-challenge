# Invera ToDo-List Challenge (Python/Django Jr-SSr)

## Project Details

In this document, we detail everything relevant to the project, including implemented packages, build process, and environment replication.

### Requirements

To run this project, you can choose between:

#### Docker Setup:
- Python 3.13
- Docker >= 20.10.13

#### Local Setup with Poetry:
- Python 3.13
- Poetry

### API Documentation

For API documentation, we are using `drf-spectacular` which provides a Swagger UI interface.

## Running with Docker (Recommended)

The easiest way to run the application is using Docker. We've provided a complete Docker setup with a Makefile for common operations.

### Getting Started with Docker

1. **Setup the environment**:
   ```bash
   make setup ENV_TYPE=docker
   ```
   This will create a `.env` file with the correct configuration for Docker.

2. **Start the containers**:
   ```bash
   make up
   ```

3. **Create a superuser**:
   ```bash
   make superuser
   ```

4. **Open API Documentation**:
   ```bash
   make open-docs
   ```
   This will open the Swagger UI in your default browser at: `http://localhost:8000/api/docs/`

5. **Seed the database with sample data** (optional):
   ```bash
   make seed_data
   ```

6. **Run tests** (optional):
    ```bash
    make test
    ```


### Other Useful Docker Commands

- **Populate with data**:
  ```bash
  make seed
  ```

- **View logs**:
  ```bash
  make logs
  ```

- **Run tests**:
  ```bash
  make test
  ```

- **Stop containers**:
  ```bash
  make down
  ```

- **Extract error logs**:
  ```bash
  make extract-error-logs
  ```

- **Clean up resources**:
  ```bash
  make clean
  ```

- **Reset environment completely**:
  ```bash
  make reset
  ```

## Running with Poetry (Without Docker)

If you prefer to run the application without Docker, you can use Poetry:

1. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```
2. **Setup the environment**:
    ```bash
   make setup ENV_TYPE=local
   ```
   This will create a `.env` file with the correct configuration for local development.

3. **Install dependencies**:
   ```bash
   poetry install
   ```

4. **Activate the virtual environment**:
   ```bash
   poetry shell
   ```

5. **Set up the database**:
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

8. **Access the API documentation**:
   Open your browser and navigate to: `http://127.0.0.1:8000/api/docs/`

9. **Seed the database with sample data** (optional):
   ```bash
   python manage.py seed_data
   ```

10. **Run tests** (optional):
    ```bash
    python manage.py test
    ```


## Authentication

You can authenticate with the application in several ways:

1. Using the Swagger UI: Click the `Authorize` button in the Swagger UI
2. Using JWT endpoint: `http://127.0.0.1:8000/api/token`
3. Using external tools:

```bash
ACCESS=$(curl -s -X POST -d "username=admin&password=admin" http://127.0.0.1:8000/api/token/ | jq -r '.access')
curl -H "Authorization: Bearer $ACCESS" http://127.0.0.1:8000/api/users/
```

## Using the Task Management API

Once you have the application running and have authenticated, you can use the API to manage tasks. Here's how to perform the main operations:

### Task Operations

#### 1. List All Tasks

You can view all tasks by accessing the tasks endpoint. You can also filter tasks by various criteria:

- **Get all tasks**:
  ```bash
  curl -H "Authorization: Bearer $ACCESS" http://localhost:8000/api/tasks/
  ```

- **Filter tasks by status** (completed/not completed):
  ```bash
  curl -H "Authorization: Bearer $ACCESS" "http://localhost:8000/api/tasks/?completed=true"
  ```

- **Filter tasks by creation date** (YYYY-MM-DD format):
  ```bash
  curl -H "Authorization: Bearer $ACCESS" "http://localhost:8000/api/tasks/?created_on=2025-8-14"
  ```

- **Search tasks by content**:
  ```bash
  curl -H "Authorization: Bearer $ACCESS" "http://localhost:8000/api/tasks/?search=meeting"
  ```

#### 2. Create a New Task

To create a new task, send a POST request to the tasks endpoint:

```bash
curl -X POST \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"description": "Finish implementing all the features"}' \
  http://localhost:8000/api/tasks/
```

#### 3. View a Specific Task

To view details of a specific task, use its ID:

```bash
curl -H "Authorization: Bearer $ACCESS" http://localhost:8000/api/tasks/1/
```

#### 4. Update a Task

To update a task, send a PATCH request:

```bash
# Mark a task as completed
curl -X PATCH \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"completed": true}' \
  http://localhost:8000/api/tasks/1/
```

#### 5. Delete a Task

To delete a task:

```bash
curl -X DELETE \
  -H "Authorization: Bearer $ACCESS" \
  http://localhost:8000/api/tasks/1/
```

### Using the Swagger UI

The easiest way to explore and use the API is through the Swagger UI:

1. Navigate to `http://localhost:8000/api/docs/`
2. Click the "Authorize" button at the top right and enter your credentials
3. Browse the available endpoints:
   - `/api/token/` - Get JWT tokens
   - `/api/token/refresh/` - Refresh JWT tokens
   - `/api/users/` - User management
   - `/api/tasks/` - Task management

For each endpoint, you can:
- Click "Try it out"
- Fill in the required parameters
- Execute the request
- View the response

This interactive documentation makes it easy to understand and test all API functionalities without writing any code.

### Pagination and Sorting

- Results are paginated with 10 items per page by default
- You can navigate pages using the `page` parameter: `?page=2`
- Tasks can be sorted by creation date, due date, or title using the `ordering` parameter:
  ```
  ?ordering=created_at
  ?ordering=-created_at  # Descending order
  ```

### Error Handling

The API returns appropriate HTTP status codes for different scenarios:
- 200: Successful operation
- 201: Resource created
- 400: Bad request (validation errors)
- 401: Unauthorized (authentication required)
- 403: Forbidden (insufficient permissions)
- 404: Resource not found
- 500: Server error

Error responses include detailed messages to help identify the issue.