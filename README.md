# Spring Kitchensink Application

This is a migrated version of the JBoss EAP Kitchensink quickstart application, now using Spring Boot with Java 21.

## Prerequisites

- Java 21 or later
- Maven 3.9.0 or later

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
   - JPA entities migrated to use Spring Data JPA
   - Repository interfaces created using Spring Data JPA

2. **Service Layer**
   - EJB components migrated to Spring Services
   - Transaction management handled by Spring's `@Transactional`

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

The application uses an in-memory H2 database by default. The H2 console is available at `/kitchensink/h2-console`.

Database connection details:
- JDBC URL: `jdbc:h2:mem:kitchensinkdb`
- Username: `sa`
- Password: (empty) 