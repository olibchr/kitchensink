# Kitchensink API Schema Documentation

This document describes the data models and schemas used in the Kitchensink API.

## Member Schema

The Member entity represents a person in the system.

### Properties

| Property     | Type   | Description                                        | Constraints                                         |
|--------------|--------|----------------------------------------------------|----------------------------------------------------|
| id           | Long   | Unique identifier for the member (auto-generated)  | Primary key                                        |
| name         | String | The name of the member                             | - Not null<br>- Size: 1-25 characters<br>- Cannot contain numbers |
| email        | String | The email address of the member                    | - Not null<br>- Not empty<br>- Valid email format<br>- Must be unique |
| phoneNumber  | String | The phone number of the member                     | - Not null<br>- Size: 10-12 characters<br>- Digits only |

### JSON Representation

```json
{
  "id": 1,
  "name": "John Smith",
  "email": "john.smith@example.com",
  "phoneNumber": "1234567890"
}
```

### Validation Rules

#### Name
- Must not be null
- Length must be between 1 and 25 characters
- Must not contain numeric characters (matching regex: "[^0-9]*")

#### Email
- Must not be null
- Must not be empty
- Must be a valid email format
- Must be unique in the system

#### Phone Number
- Must not be null
- Length must be between 10 and 12 characters
- Must contain only digits

## Database Schema

The Member entity is mapped to a database table with the following structure:

### Member Table

| Column         | Type         | Constraints                |
|----------------|--------------|----------------------------|
| id             | BIGINT       | Primary Key, Auto Increment |
| name           | VARCHAR(25)  | Not Null                   |
| email          | VARCHAR(255) | Not Null, Unique           |
| phone_number   | VARCHAR(12)  | Not Null                   |

## Entity-Relationship Diagram

```
┌─────────────────────┐
│     Member          │
├─────────────────────┤
│ id: Long (PK)       │
│ name: String        │
│ email: String       │
│ phone_number: String│
└─────────────────────┘
``` 