# Spring Kitchensink Application

This is a migrated version of the JBoss EAP Kitchensink quickstart application, now using Spring Boot with Java 21 and MongoDB.

## Prerequisites

- Java 21 or later
- Maven 3.9.0 or later
- MongoDB (optional, as embedded MongoDB is included)

## Building and Running the Application

### Building the Application

```bash
mvn clean package
```

### Running the Application

```bash
mvn spring-boot:run
```

The application will be available at: http://localhost:8080/kitchensink/

## Key Migration Points

This application has been migrated from a traditional JBoss EAP application to Spring Boot with the following changes:

1. **Data Layer**
   - JPA entities migrated to MongoDB documents
   - Repository interfaces created using Spring Data MongoDB
   - Embedded MongoDB for development and testing

2. **Service Layer**
   - EJB components migrated to Spring Services
   - Transaction management handled by MongoDB's transactions

3. **REST API**
   - JAX-RS endpoints migrated to Spring REST Controllers
   - Same API contracts maintained

4. **UI Layer**
   - JSF views replaced with Thymeleaf templates
   - Modern Bootstrap styling

5. **Configuration**
   - XML-based configuration replaced with Java configuration and properties

## API Endpoints

- List all members: GET `/kitchensink/api/members`
- Get member by ID: GET `/kitchensink/api/members/{id}`
- Create member: POST `/kitchensink/api/members`

## Database

The application uses MongoDB for data storage. By default, it uses an embedded MongoDB instance running on port 27018.

MongoDB connection details:
- Host: `localhost`
- Port: `27018`
- Database: `kitchensinkdb`

## Documentation

The documentation folder contains comprehensive information about the application:

- **API Documentation**: Detailed OpenAPI specifications in `openapi.yaml` for all REST endpoints
- **Data Models**: Visual representation of data models using Mermaid diagrams in `data-models.md`
- **API Schema**: Details of data schemas and validation rules in `API_SCHEMA.md`
- **MongoDB Migration**: Guidelines and steps for MongoDB migration in `mongodb-migration.md`

## Measurement Scripts

The project includes various measurement scripts in the `measurements` folder that analyze code quality:

### Documentation Analysis (`documentation.py`)
Analyzes the quality and completeness of project documentation, including:
- JavaDoc coverage for classes and methods
- README quality assessment
- Code comment ratio
- API documentation quality

### Security Analysis (`security.py`)
Performs security checks on the codebase, including:
- Outdated and vulnerable dependencies
- Static code security analysis
- Vulnerability assessment by severity level

### Complexity Analysis (`complexity.py`)
Measures code complexity metrics, including:
- Average method length and cyclomatic complexity
- Dependency count and analysis
- Configuration complexity

### Correctness Analysis (`correctnes.py`)
Evaluates code correctness through:
- Code coverage analysis
- Test quality assessment
- Critical path coverage
- Data store testing coverage

To run a measurement script:
```bash
python measurements/documentation.py 