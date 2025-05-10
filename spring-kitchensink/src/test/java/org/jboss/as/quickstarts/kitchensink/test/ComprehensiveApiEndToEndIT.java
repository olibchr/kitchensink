/*
 * Original JBoss, Home of Professional Open Source
 * Copyright 2015, Red Hat, Inc. and/or its affiliates, and individual
 * contributors by the @authors tag.
 * 
 * Migrated to Spring Boot
 */
package org.jboss.as.quickstarts.kitchensink.test;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.junit.jupiter.SpringExtension;

import jakarta.json.Json;
import jakarta.json.JsonArray;
import jakarta.json.JsonObject;
import jakarta.json.JsonReader;
import jakarta.json.JsonValue;

import java.io.StringReader;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Optional;
import java.util.UUID;
import java.util.logging.Logger;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Run a comprehensive test of all API endpoints with various test cases
 */
@ExtendWith(SpringExtension.class)
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
public class ComprehensiveApiEndToEndIT {

    private static final Logger log = Logger.getLogger(ComprehensiveApiEndToEndIT.class.getName());
    private final HttpClient httpClient = HttpClient.newHttpClient();

    @LocalServerPort
    private int port;

    private URI baseUri;

    @BeforeEach
    public void setup() throws URISyntaxException {
        this.baseUri = new URI("http://localhost:" + port + "/kitchensink/rest/members");
    }

    @Test
    public void testAllEndpoints() throws Exception {
        log.info("Starting comprehensive API testing");

        // Test the GET /members endpoint
        log.info("Testing GET /members endpoint");
        testGetAllMembers();

        // Test the POST /members endpoint with valid data
        log.info("Testing POST /members endpoint with valid data");
        String uniqueId = UUID.randomUUID().toString().substring(0, 8);
        String uniqueEmail = "comprehensive." + uniqueId + "@example.com";

        JsonObject newMemberJson = Json.createObjectBuilder()
                .add("name", "Comprehensive Test")
                .add("email", uniqueEmail)
                .add("phoneNumber", "1234567890")
                .build();

        HttpRequest createRequest = HttpRequest.newBuilder(baseUri)
                .header("Content-Type", "application/json")
                .header("Accept", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(newMemberJson.toString()))
                .build();

        HttpResponse<String> createResponse = httpClient.send(createRequest, HttpResponse.BodyHandlers.ofString());
        assertEquals(200, createResponse.statusCode(), "Member creation should succeed");

        // Get all members and find the newly created one
        HttpRequest getAllRequest = HttpRequest.newBuilder(baseUri)
                .header("Accept", "application/json")
                .GET()
                .build();

        HttpResponse<String> getAllResponse = httpClient.send(getAllRequest, HttpResponse.BodyHandlers.ofString());
        JsonArray members = parseJsonArray(getAllResponse.body());

        Optional<Long> newMemberId = findMemberIdByEmail(members, uniqueEmail);
        assertTrue(newMemberId.isPresent(), "New member should exist in the list");

        // Test the GET /members/{id} endpoint
        log.info("Testing GET /members/{id} endpoint with valid ID: " + newMemberId.get());
        URI memberUri = new URI(baseUri.toString() + "/" + newMemberId.get());
        HttpRequest getMemberRequest = HttpRequest.newBuilder(memberUri)
                .header("Accept", "application/json")
                .GET()
                .build();

        HttpResponse<String> getMemberResponse = httpClient.send(getMemberRequest,
                HttpResponse.BodyHandlers.ofString());
        assertEquals(200, getMemberResponse.statusCode());

        // Test some error cases

        // 1. Non-existent ID
        log.info("Testing GET /members/{id} with non-existent ID");
        URI nonExistentUri = new URI(baseUri.toString() + "/999999");
        HttpRequest getNonExistentRequest = HttpRequest.newBuilder(nonExistentUri)
                .header("Accept", "application/json")
                .GET()
                .build();

        HttpResponse<String> getNonExistentResponse = httpClient.send(getNonExistentRequest,
                HttpResponse.BodyHandlers.ofString());
        assertEquals(404, getNonExistentResponse.statusCode());

        // 2. Invalid member data (empty name)
        log.info("Testing POST /members with invalid data (empty name)");
        JsonObject invalidMemberJson = Json.createObjectBuilder()
                .add("name", "")
                .add("email", "invalid@example.com")
                .add("phoneNumber", "1234567890")
                .build();

        HttpRequest createInvalidRequest = HttpRequest.newBuilder(baseUri)
                .header("Content-Type", "application/json")
                .header("Accept", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(invalidMemberJson.toString()))
                .build();

        HttpResponse<String> createInvalidResponse = httpClient.send(createInvalidRequest,
                HttpResponse.BodyHandlers.ofString());
        assertEquals(400, createInvalidResponse.statusCode());

        // 3. Duplicate email
        log.info("Testing POST /members with duplicate email");
        JsonObject duplicateEmailJson = Json.createObjectBuilder()
                .add("name", "Duplicate User")
                .add("email", uniqueEmail) // Reuse the email from earlier
                .add("phoneNumber", "1234567890")
                .build();

        HttpRequest createDuplicateRequest = HttpRequest.newBuilder(baseUri)
                .header("Content-Type", "application/json")
                .header("Accept", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(duplicateEmailJson.toString()))
                .build();

        HttpResponse<String> createDuplicateResponse = httpClient.send(createDuplicateRequest,
                HttpResponse.BodyHandlers.ofString());
        assertEquals(409, createDuplicateResponse.statusCode());

        // 4. Invalid JSON
        log.info("Testing POST /members with invalid JSON format");
        String invalidJson = "{name: 'Missing quotes', email: missing.quotes@example.com}";

        HttpRequest createWithInvalidJsonRequest = HttpRequest.newBuilder(baseUri)
                .header("Content-Type", "application/json")
                .header("Accept", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(invalidJson))
                .build();

        HttpResponse<String> invalidJsonResponse = httpClient.send(createWithInvalidJsonRequest,
                HttpResponse.BodyHandlers.ofString());
        assertEquals(400, invalidJsonResponse.statusCode(), "Invalid JSON should return 400 Bad Request");

        log.info("Comprehensive API testing completed successfully");
    }

    private void testGetAllMembers() throws Exception {
        HttpRequest getAllRequest = HttpRequest.newBuilder(baseUri)
                .header("Accept", "application/json")
                .GET()
                .build();

        HttpResponse<String> response = httpClient.send(getAllRequest, HttpResponse.BodyHandlers.ofString());

        assertEquals(200, response.statusCode(), "Should return status 200");

        // Verify the response is a valid JSON array
        JsonArray members = parseJsonArray(response.body());

        // Verify each member has the required fields (if any members exist)
        for (JsonValue value : members) {
            JsonObject member = value.asJsonObject();
            assertTrue(member.containsKey("id"), "Member should have an ID");
            assertTrue(member.containsKey("name"), "Member should have a name");
            assertTrue(member.containsKey("email"), "Member should have an email");
            assertTrue(member.containsKey("phoneNumber"), "Member should have a phone number");
        }
    }

    private JsonArray parseJsonArray(String json) {
        try (JsonReader reader = Json.createReader(new StringReader(json))) {
            return reader.readArray();
        }
    }

    private JsonObject parseJsonObject(String json) {
        try (JsonReader reader = Json.createReader(new StringReader(json))) {
            return reader.readObject();
        }
    }

    private Optional<Long> findMemberIdByEmail(JsonArray members, String email) {
        for (JsonValue value : members) {
            JsonObject member = value.asJsonObject();
            if (email.equals(member.getString("email"))) {
                return Optional.of(member.getJsonNumber("id").longValue());
            }
        }
        return Optional.empty();
    }
}