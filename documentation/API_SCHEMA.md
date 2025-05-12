# Kitchensink API Schema Documentation

This document describes the data models and schemas used in the Kitchensink API.

## Member Schema

The Member entity represents a person in the system.

### Properties

| Property     | Type     | Description                                        | Constraints                                         |
|--------------|----------|----------------------------------------------------|----------------------------------------------------|
| _id          | ObjectId | Unique identifier for the member (auto-generated)  | Primary key                                        |
| name         | String   | The name of the member                             | - Not null<br>- Size: 1-25 characters<br>- Cannot contain numbers |
| email        | String   | The email address of the member                    | - Not null<br>- Not empty<br>- Valid email format<br>- Must be unique |
| phoneNumber  | String   | The phone number of the member                     | - Not null<br>- Size: 10-12 characters<br>- Digits only |
| createdAt    | ISODate  | Timestamp when the document was created            | Auto-generated                                      |
| updatedAt    | ISODate  | Timestamp when the document was last updated       | Auto-updated on modification                        |

### JSON Representation

```json
{
  "_id": "60a6f63d5f8ee27e1a61dea4",
  "name": "John Smith",
  "email": "john.smith@example.com",
  "phoneNumber": "1234567890",
  "createdAt": "2023-05-01T12:00:00.000Z",
  "updatedAt": "2023-05-01T12:00:00.000Z"
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

## MongoDB Schema

The Member entity is mapped to a MongoDB collection with the following structure:

### Member Collection

| Field          | Type     | Constraints                |
|----------------|----------|----------------------------|
| _id            | ObjectId | Primary Key                |
| name           | String   | Not Null                   |
| email          | String   | Not Null, Unique           |
| phoneNumber    | String   | Not Null                   |
| createdAt      | ISODate  | Auto-generated             |
| updatedAt      | ISODate  | Auto-updated               |

## Collection Schema Diagram
┌──────────────────────────┐
│ Member │
├──────────────────────────┤
│ id: ObjectId (PK) │
│ name: String │
│ email: String (UK) │
│ phoneNumber: String │
│ createdAt: ISODate │
│ updatedAt: ISODate │
└──────────────────────────┘


## MongoDB Indexes

| Index Name   | Fields       | Type    | Description                    |
|--------------|--------------|---------|--------------------------------|
| _id          | { _id: 1 }   | Default | Default MongoDB _id index      |
| email_unique | { email: 1 } | Unique  | Ensures email uniqueness       |
| name_index   | { name: 1 }  | Regular | Optimizes sorting by name      |