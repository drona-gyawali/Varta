# Varta Authentication API Documentation

This document outlines the authentication-related endpoints for a Varta system. The API provides functionality for user registration, login, profile retrieval, KYC (Know Your Customer) verification, and logout. All endpoints are prefixed with `/api/v1` and tagged under `Auth`.

## Base URL
```
/api/v1
```

## Endpoints

### 1. Register
- **Endpoint**: `POST /register`
- **Description**: Registers a new user with an email and password.
- **Request Body**:
  ```json
  {
    "email": "string",
    "password": "string"
  }
  ```
- **Responses**:
  - **201 Created**:
    ```json
    {
      "success": 201,
      "message": "Registration was successful"
    }
    ```
  - **400 Bad Request**:
    ```json
    {
      "success": 400,
      "msg": "User email already exists in the system"
    }
    ```
  - **400 Bad Request (Validation Error)**:
    ```json
    {
      "detail": "Validation error message"
    }
    ```
- **Dependencies**: Async SQLAlchemy session (`DbInstance.get_db`)

### 2. Login
- **Endpoint**: `POST /login`
- **Description**: Authenticates a user and sets a secure access token cookie.
- **Request Body**: Form data (OAuth2PasswordRequestForm)
  - `username`: User's email
  - `password`: User's password
- **Responses**:
  - **200 OK**:
    ```json
    {
      "success": 200,
      "message": "Login Successful"
    }
    ```
    - Sets a secure HTTP-only cookie: `access_token`
  - **401 Unauthorized**:
    ```json
    {
      "failure": 401,
      "msg": "Wrong Credentials has been passed"
    }
    ```
  - **500 Internal Server Error**:
    ```json
    {
      "detail": "Internal Server Error"
    }
    ```
- **Dependencies**: Async SQLAlchemy session (`DbInstance.get_db`)

### 3. Profile Details
- **Endpoint**: `GET /profile_details`
- **Description**: Retrieves the authenticated user's profile details.
- **Response Model**: `ProfileDetails`
  ```json
  {
    "success": 200,
    "id": "string",
    "email": "string",
    "profileUrl": "string",
    "createdAt": "string (ISO 8601)"
  }
  ```
- **Responses**:
  - **200 OK**: Returns user profile details.
  - **400 Bad Request**:
    ```json
    {
      "detail": "Error while fetching profile view"
    }
    ```
  - **500 Internal Server Error**:
    ```json
    {
      "detail": "Internal Server Error"
    }
    ```
- **Dependencies**:
  - Async SQLAlchemy session (`DbInstance.get_db`)
  - Authenticated user (`get_current_user`)

### 4. KYC (Know Your Customer)
- **Endpoint**: `GET /kyc/{user_id}`
- **Description**: Retrieves profile details for a specific user by ID (e.g., for KYC verification).
- **Path Parameters**:
  - `user_id`: String, the ID of the user
- **Response Model**: `ProfileDetails`
  ```json
  {
    "success": 200,
    "id": "string",
    "email": "string",
    "profileUrl": "string",
    "createdAt": "string (ISO 8601)"
  }
  ```
- **Responses**:
  - **200 OK**: Returns user profile details.
  - **400 Bad Request**:
    ```json
    {
      "detail": "Error while fetching profile view"
    }
    ```
  - **500 Internal Server Error**:
    ```json
    {
      "detail": "Internal Server Error"
    }
    ```
- **Dependencies**: Async SQLAlchemy session (`DbInstance.get_db`)

### 5. Logout
- **Endpoint**: `POST /logout`
- **Description**: Logs out the user by clearing the access token cookie.
- **Responses**:
  - **200 OK**:
    ```json
    {
      "message": "Logged out successfully"
    }
    ```
  - **500 Internal Server Error**:
    ```json
    {
      "detail": "Internal Server Error"
    }
    ```
- **Dependencies**: None

## Notes
- **Authentication**: The `/profile_details` endpoint requires a valid `access_token` cookie, set during login and verified via the `get_current_user` dependency.
- **Security**: The login endpoint sets an HTTP-only, secure cookie (`access_token`) with `samesite="none"` to support cross-origin requests.
- **Error Handling**: All endpoints include logging for debugging and return appropriate HTTP status codes for errors.
- **Database**: Uses async SQLAlchemy for non-blocking database operations.
- **Future Improvements**: A refresh token endpoint is planned (see `TODO` in code).

This API is designed to be secure, scalable, and maintainable, leveraging FastAPI's async capabilities and modern security practices. For further details on implementation, refer to the source code or contact the developer.

----


# Messaging API Documentation

This document outlines the messaging-related endpoints for a FastAPI-based system. The API provides functionality for creating and managing chat rooms, joining rooms, generating invitation links, retrieving room members, and sending/retrieving messages. All endpoints are prefixed with `/api/v1` and tagged under `Message`.

## Base URL
```
/api/v1
```

## Endpoints

### 1. Create Room
- **Endpoint**: `POST /create-rooms`
- **Description**: Creates a new chat room (public or private).
- **Request Body**:
  ```json
  {
    "room_name": "string",
    "is_private": boolean
  }
  ```
- **Responses**:
  - **200 OK**:
    ```json
    {
      "success": 200,
      "msg": "Room created successfully"
    }
    ```
  - **400 Bad Request**:
    ```json
    {
      "failure": 400,
      "msg": "Error occurred while creating room"
    }
    ```
  - **401 Unauthorized**:
    ```json
    {
      "failure": 401,
      "msg": "Unauthorized access forbidden"
    }
    ```
  - **500 Internal Server Error**:
    ```json
    {
      "detail": "Internal Server Error"
    }
    ```
- **Dependencies**:
  - Authenticated user (`get_current_user`)
  - Async SQLAlchemy session (`DbInstance.get_db`)

### 2. Get All Rooms
- **Endpoint**: `GET /rooms`
- **Description**: Retrieves a list of rooms accessible to the authenticated user.
- **Responses**:
  - **200 OK**:
    ```json
    {
      "success": 200,
      "data": [
        {
          "id": "string",
          "room_name": "string",
          "is_private": boolean,
          // Additional room fields
        }
      ]
    }
    ```
  - **400 Bad Request**:
    ```json
    {
      "failure": 400,
      "msg": "No rooms found or error occurred while fetching"
    }
    ```
  - **401 Unauthorized**:
    ```json
    {
      "failure": 401,
      "msg": "Unauthorized access"
    }
    ```
  - **500 Internal Server Error**:
    ```json
    {
      "detail": "Internal Server Error"
    }
    ```
- **Dependencies**:
  - Authenticated user (`get_current_user`)
  - Async SQLAlchemy session (`DbInstance.get_db`)

### 3. Get Room Details
- **Endpoint**: `GET /rooms/{id}`
- **Description**: Retrieves details of a specific room and its members.
- **Path Parameters**:
  - `id`: String, the ID of the room
- **Responses**:
  - **200 OK**:
    ```json
    {
      "success": 200,
      "room_data": {
        "id": "string",
        "room_name": "string",
        "is_private": boolean,
        "members": [
          {
            "id": "string",
            "email": "string",
            // Additional user fields
          }
        ]
      }
    }
    ```
  - **400 Bad Request**:
    ```json
    {
      "detail": "Error message (e.g., Invalid room ID)"
    }
    ```
  - **403 Forbidden**:
    ```json
    {
      "detail": "Forbidden User"
    }
    ```
  - **500 Internal Server Error**:
    ```json
    {
      "detail": "Internal Server Error"
    }
    ```
- **Dependencies**:
  - Authenticated user (`get_current_user`)
  - Async SQLAlchemy session (`DbInstance.get_db`)

### 4. Join Room
- **Endpoint**: `POST /rooms/{id}/join`
- **Description**: Allows a user to join a room using an invite token (for private rooms).
- **Path Parameters**:
  - `id`: String, the ID of the room
- **Request Body**:
  ```json
  {
    "invite_token": "string"
  }
  ```
- **Responses**:
  - **200 OK**:
    ```json
    {
      "success": 200,
      "msg": "User successfully joined room"
    }
    ```
  - **400 Bad Request**:
    ```json
    {
      "failure": 400,
      "msg": "Error occurred while joining room"
    }
    ```
  - **400 Bad Request (Validation Error)**:
    ```json
    {
      "detail": "Error message (e.g., Invalid invite token)"
    }
    ```
  - **401 Unauthorized**:
    ```json
    {
      "failure": 401,
      "msg": "Unauthorized access"
    }
    ```
  - **500 Internal Server Error**:
    ```json
    {
      "detail": "Internal Server Error"
    }
    ```
- **Dependencies**:
  - Authenticated user (`get_current_user`)
  - Async SQLAlchemy session (`DbInstance.get_db`)

### 5. Create Invitation Link
- **Endpoint**: `POST /rooms/{id}/invite`
- **Description**: Generates an invitation token for a private room.
- **Path Parameters**:
  - `id`: String, the ID of the room
- **Responses**:
  - **200 OK**:
    ```json
    {
      "status": 200,
      "invitation_token": "string"
    }
    ```
  - **400 Bad Request**:
    ```json
    {
      "status": 400,
      "invitation_token": "Public room cannot create token"
    }
    ```
  - **400 Bad Request (Validation Error)**:
    ```json
    {
      "detail": "Error message (e.g., Invalid room ID)"
    }
    ```
  - **403 Forbidden**:
    ```json
    {
      "detail": "Forbidden User"
    }
    ```
  - **500 Internal Server Error**:
    ```json
    {
      "detail": "Internal Server Error"
    }
    ```
- **Dependencies**:
  - Authenticated user (`get_current_user`)
  - Async SQLAlchemy session (`DbInstance.get_db`)

### 6. Get Room Members
- **Endpoint**: `GET /rooms/{id}/members`
- **Description**: Retrieves a list of members in a specific room.
- **Path Parameters**:
  - `id`: String, the ID of the room
- **Responses**:
  - **200 OK**:
    ```json
    {
      "success": 200,
      "data": [
        {
          "id": "string",
          "email": "string",
          // Additional user fields
        }
      ]
    }
    ```
  - **400 Bad Request**:
    ```json
    {
      "failure": 400,
      "msg": "Error occurred while fetching member data"
    }
    ```
  - **401 Unauthorized**:
    ```json
    {
      "failure": 401,
      "msg": "Unauthorized access"
    }
    ```
  - **500 Internal Server Error**:
    ```json
    {
      "detail": "Internal Server Error"
    }
    ```
- **Dependencies**:
  - Authenticated user (`get_current_user`)
  - Async SQLAlchemy session (`DbInstance.get_db`)

### 7. Get Room Messages
- **Endpoint**: `GET /room/messages/`
- **Description**: Fetches messages for a specific room with pagination support.
- **Query Parameters**:
  - `room_id`: Optional string, filter messages by room ID
  - `limit`: Integer (1–100), number of messages to return (default: 20)
  - `offset`: Integer (>=0), number of messages to skip (default: 0)
- **Responses**:
  - **200 OK**:
    ```json
    {
      "success": 200,
      "messages": [
        {
          "id": "string",
          "text": "string",
          "user_id": "string",
          "room_id": "string",
          "created_at": "string (ISO 8601)",
          // Additional message fields
        }
      ]
    }
    ```
  - **400 Bad Request**:
    ```json
    {
      "failure": 400,
      "msg": "Error occurred while fetching messages"
    }
    ```
  - **401 Unauthorized**:
    ```json
    {
      "failure": 401,
      "msg": "Unauthorized access"
    }
    ```
  - **500 Internal Server Error**:
    ```json
    {
      "detail": "Internal Server Error"
    }
    ```
- **Dependencies**:
  - Authenticated user (`get_current_user`)
  - Async SQLAlchemy session (`DbInstance.get_db`)

### 8. Create Message
- **Endpoint**: `POST /room/create-message`
- **Description**: Sends a new message to a specific room.
- **Request Body**:
  ```json
  {
    "text": "string",
    "room_id": "string"
  }
  ```
- **Responses**:
  - **200 OK**:
    ```json
    {
      "success": 200,
      "msg": "message created successfully"
    }
    ```
  - **400 Bad Request**:
    ```json
    {
      "failure": 400,
      "msg": "Error occurred while creating message"
    }
    ```
  - **401 Unauthorized**:
    ```json
    {
      "failure": 401,
      "msg": "Unauthorized access"
    }
    ```
  - **500 Internal Server Error**:
    ```json
    {
      "detail": "Internal Server Error"
    }
    ```
- **Dependencies**:
  - Authenticated user (`get_current_user`)
  - Async SQLAlchemy session (`DbInstance.get_db`)

## Notes
- **Authentication**: All endpoints require a valid `access_token` cookie, verified via the `get_current_user` dependency.
- **Security**: Access to rooms and messages is restricted to authorized users, with additional checks for private rooms (e.g., invite tokens).
- **Error Handling**: Endpoints include logging for debugging and return appropriate HTTP status codes for errors, including specific handling for `PermissionError` and `ValueError`.
- **Database**: Uses async SQLAlchemy for non-blocking database operations.
- **Pagination**: The `/room/messages/` endpoint supports pagination via `limit` and `offset` query parameters.
- **Private Rooms**: Private rooms require an invite token to join, and only authorized users can generate invitation links.

This API is designed for secure, scalable chat functionality, leveraging FastAPI's async capabilities and robust error handling. For further details on implementation, refer to the source code or contact the developer.