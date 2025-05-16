/*
 * Original JBoss, Home of Professional Open Source
 * Copyright 2015, Red Hat, Inc. and/or its affiliates, and individual
 * contributors by the @authors tag.
 * 
 * Migrated to Spring Boot
 */
package org.jboss.as.quickstarts.kitchensink.test;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.extension.ExtendWith;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.MethodSource;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.junit.jupiter.SpringExtension;

import jakarta.json.Json;
import jakarta.json.JsonObject;
import jakarta.json.JsonObjectBuilder;
import jakarta.json.JsonReader;

import java.io.StringReader;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.UUID;
import java.util.logging.Logger;
import java.util.stream.Stream;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Parameterized test class for testing the POST /members endpoint
 * with different input scenarios
 */
@ExtendWith(SpringExtension.class)
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
public class CreateMemberEndToEndIT {

    private static final Logger log = Logger.getLogger(CreateMemberEndToEndIT.class.getName());
    private final HttpClient httpClient = HttpClient.newHttpClient();

    @LocalServerPort
    private int port;

    private URI baseUri;

    @BeforeEach
    public void setup() throws URISyntaxException {
        this.baseUri = new URI("http://localhost:" + port + "/kitchensink/rest/members");
    }

    @ParameterizedTest(name = "{5}")
    @MethodSource("createMemberTestData")
    public void testCreateMember(String name, String email, String phoneNumber,
            int expectedStatus, String expectedValidationField, String testDescription) throws Exception {
        log.info("Testing POST /members: " + testDescription);

        // For duplicate email test, first create a member with that email
        if (testDescription.equals("Duplicate email")) {
            JsonObject firstMemberJson = Json.createObjectBuilder()
                    .add("name", "First User")
                    .add("email", email)
                    .add("phoneNumber", "1234567890")
                    .build();

            HttpRequest firstCreateRequest = HttpRequest.newBuilder(baseUri)
                    .header("Content-Type", "application/json")
                    .header("Accept", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(firstMemberJson.toString()))
                    .build();

            httpClient.send(firstCreateRequest, HttpResponse.BodyHandlers.ofString());
        }

        // Special case for invalid JSON test
        if (testDescription.equals("Invalid JSON format")) {
            String invalidJson = "{name: 'Missing quotes', email: missing.quotes@example.com}";

            HttpRequest createInvalidRequest = HttpRequest.newBuilder(baseUri)
                    .header("Content-Type", "application/json")
                    .header("Accept", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(invalidJson))
                    .build();

            HttpResponse<String> response = httpClient.send(createInvalidRequest,
                    HttpResponse.BodyHandlers.ofString());
            assertEquals(400, response.statusCode(), "Invalid JSON should return status 400");
            return;
        }

        // Create the test member
        JsonObjectBuilder jsonBuilder = Json.createObjectBuilder();

        // Only add non-null fields
        if (name != null) {
                jsonBuilder.add("name", name);
        } else {
                jsonBuilder.addNull("name"); // Use addNull for null values
        }

        if (email != null) {
                jsonBuilder.add("email", email);
        } else {
                jsonBuilder.addNull("email");
        }

        if (phoneNumber != null) {
                jsonBuilder.add("phoneNumber", phoneNumber);
        } else {
                jsonBuilder.addNull("phoneNumber");
        }

        JsonObject memberJson = jsonBuilder.build();

        HttpRequest createRequest = HttpRequest.newBuilder(baseUri)
                .header("Content-Type", "application/json")
                .header("Accept", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(memberJson.toString()))
                .build();

        HttpResponse<String> response = httpClient.send(createRequest, HttpResponse.BodyHandlers.ofString());

        assertEquals(expectedStatus, response.statusCode(),
                "Status code should match expected for " + testDescription);

        // For error cases, check that the expected validation field is in the response
        if (expectedStatus != 200 && expectedValidationField != null) {
            // Only parse if response body is not empty
            if (!response.body().isEmpty()) {
                JsonObject errorResponse = parseJsonObject(response.body());
                assertTrue(errorResponse.containsKey(expectedValidationField),
                        "Response should contain validation error for '" + expectedValidationField + "'");
            }
        }
    }

    static Stream<Object[]> createMemberTestData() {
        return Stream.of(
                // Valid case
                new Object[] {
                        "Valid User",
                        "valid" + UUID.randomUUID().toString().substring(0, 8) + "@example.com",
                        "1234567890",
                        200,
                        null,
                        "Valid member data"
                },

                // Invalid cases - name validation
                new Object[] {
                        "",
                        "invalid1@example.com",
                        "1234567890",
                        400,
                        "name",
                        "Empty name"
                },
                new Object[] {
                        null,
                        "invalid1@example.com",
                        "1234567890",
                        400,
                        "name",
                        "Null name"
                },

                // Invalid cases - email validation
                new Object[] {
                        "Valid Name",
                        "notanemail",
                        "1234567890",
                        400,
                        "email",
                        "Invalid email format"
                },
                new Object[] {
                        "Valid Name",
                        "",
                        "1234567890",
                        400,
                        "email",
                        "Empty email"
                },
                new Object[] {
                        "Valid Name",
                        null,
                        "1234567890",
                        400,
                        "email",
                        "Null email"
                },

                // Invalid cases - phone validation
                new Object[] {
                        "Valid Name",
                        "valid" + UUID.randomUUID().toString().substring(0, 8) + "@example.com",
                        "123",
                        400,
                        "phoneNumber",
                        "Phone number too short"
                },
                new Object[] {
                        "Valid Name",
                        "valid" + UUID.randomUUID().toString().substring(0, 8) + "@example.com",
                        "12345678901234567890",
                        400,
                        "phoneNumber",
                        "Phone number too long"
                },
                new Object[] {
                        "Valid Name",
                        "valid" + UUID.randomUUID().toString().substring(0, 8) + "@example.com",
                        "123-456-7890",
                        400,
                        "phoneNumber",
                        "Phone number with non-digits"
                },

                // Duplicate email test
                new Object[] {
                        "Valid Name",
                        "duplicate@example.com",
                        "1234567890",
                        409,
                        "email",
                        "Duplicate email"
                });
    }

    private JsonObject parseJsonObject(String json) {
        try (JsonReader reader = Json.createReader(new StringReader(json))) {
            return reader.readObject();
        }
    }
}