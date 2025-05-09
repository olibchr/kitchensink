# Kitchensink API Documentation

Welcome to the Kitchensink API documentation. This folder contains comprehensive documentation on the REST API endpoints and data models used in the application.

## Contents

- [OpenAPI Specification](openapi.yaml) - The official OpenAPI 3.1 specification for the API
- [Data Models](data-models.md) - Visual representation of the data models using Mermaid diagrams

## Overview

The Kitchensink application provides a simple RESTful API for managing member information. The API allows you to:

- Retrieve a list of all members
- Retrieve a specific member by ID
- Create new members

All API requests and responses use JSON format. The base URL for all API endpoints is `/rest`.

## Getting Started

To use the API, you can make HTTP requests to the appropriate endpoints. For example:

```
GET /rest/members
```

For the most accurate and up-to-date API reference, please refer to the [OpenAPI specification](openapi.yaml).

## Authentication

The API currently does not require authentication.

## Support

For issues or questions about the API, please refer to the project's main README file. 