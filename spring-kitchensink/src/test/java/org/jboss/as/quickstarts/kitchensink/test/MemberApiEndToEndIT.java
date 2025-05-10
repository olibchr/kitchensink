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
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.MethodSource;
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
import java.util.stream.Stream;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * End-to-end integration test for the Member REST API
 * Tests all main API operations defined in the API:
 * - List all members
 * - Create a new member
 * - Get a specific member by ID
 */
@ExtendWith(SpringExtension.class)
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
public class MemberApiEndToEndIT {

    private static final Logger log = Logger.getLogger(MemberApiEndToEndIT.class.getName());
    private final HttpClient httpClient = HttpClient.newHttpClient();

    @LocalServerPort
    private int port;

    private URI baseUri;

    @BeforeEach
    public void setup() throws URISyntaxException {
        this.baseUri = new URI("http://localhost:" + port + "/kitchensink/rest/members");
    }

    @Test
    public void testMemberLifecycle() throws Exception {
        // Step 1: Get initial list of members
        log.info("Step 1: Getting initial list of members");
        HttpRequest getAllRequest = HttpRequest.newBuilder(baseUri)
                .header("Accept", "application/json")
                .GET()
                .build();

        HttpResponse<String> getAllResponse = httpClient.send(getAllRequest, HttpResponse.BodyHandlers.ofString());
        assertEquals(200, getAllResponse.statusCode());

        // Parse the initial response
        JsonArray initialMembers = parseJsonArray(getAllResponse.body());
        int initialCount = initialMembers.size();
        log.info("Initial member count: " + initialCount);

        // Step 2: Create a new member
        log.info("Step 2: Creating a new member");
        // Generate a unique email with UUID to avoid conflicts
        String uniqueId = UUID.randomUUID().toString().substring(0, 8);
        String uniqueEmail = "test." + uniqueId + "@example.com";

        JsonObject newMemberJson = Json.createObjectBuilder()
                .add("name", "Test Member")
                .add("email", uniqueEmail)
                .add("phoneNumber", "1234567890")
                .build();

        HttpRequest createRequest = HttpRequest.newBuilder(baseUri)
                .header("Content-Type", "application/json")
                .header("Accept", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(newMemberJson.toString()))
                .build();

        HttpResponse<String> createResponse = httpClient.send(createRequest, HttpResponse.BodyHandlers.ofString());
        assertEquals(200, createResponse.statusCode(), "Member creation should succeed with status 200");

        // Step 3: Get the updated list of members
        log.info("Step 3: Getting updated list of members");
        HttpResponse<String> updatedGetAllResponse = httpClient.send(getAllRequest,
                HttpResponse.BodyHandlers.ofString());
        assertEquals(200, updatedGetAllResponse.statusCode());

        JsonArray updatedMembers = parseJsonArray(updatedGetAllResponse.body());
        assertEquals(initialCount + 1, updatedMembers.size(), "Member count should increase by 1");

        // Find the new member in the list and get its ID
        Optional<Long> newMemberId = findMemberIdByEmail(updatedMembers, uniqueEmail);
        assertTrue(newMemberId.isPresent(), "New member should exist in the updated list");

        // Step 4: Get the specific member by ID
        log.info("Step 4: Getting the new member by ID: " + newMemberId.get());
        URI memberUri = new URI(baseUri.toString() + "/" + newMemberId.get());
        HttpRequest getMemberRequest = HttpRequest.newBuilder(memberUri)
                .header("Accept", "application/json")
                .GET()
                .build();

        HttpResponse<String> getMemberResponse = httpClient.send(getMemberRequest,
                HttpResponse.BodyHandlers.ofString());
        assertEquals(200, getMemberResponse.statusCode());

        JsonObject member = parseJsonObject(getMemberResponse.body());
        assertEquals(newMemberId.get().longValue(), member.getJsonNumber("id").longValue(), "Member ID should match");
        assertEquals("Test Member", member.getString("name"), "Member name should match");
        assertEquals(uniqueEmail, member.getString("email"), "Member email should match");
        assertEquals("1234567890", member.getString("phoneNumber"), "Member phone should match");

        log.info("End-to-end API test completed successfully");
    }

    /**
     * Get Member By ID parameterized test
     */
    @ParameterizedTest(name = "{2}")
    @MethodSource("getMemberByIdTestData")
    public void testGetMemberById(long memberId, int expectedStatus, String testDescription) throws Exception {
        log.info("Testing GET /members/{id}: " + testDescription);

        // For the "valid ID" test case, we need to find a valid ID first
        long idToTest = memberId;

        if (expectedStatus == 200) {
            // First create a member to get a valid ID
            String uniqueId = UUID.randomUUID().toString().substring(0, 8);
            String uniqueEmail = "valid." + uniqueId + "@example.com";

            JsonObject newMemberJson = Json.createObjectBuilder()
                    .add("name", "Valid Test")
                    .add("email", uniqueEmail)
                    .add("phoneNumber", "1234567890")
                    .build();

            HttpRequest createRequest = HttpRequest.newBuilder(baseUri)
                    .header("Content-Type", "application/json")
                    .header("Accept", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(newMemberJson.toString()))
                    .build();

            httpClient.send(createRequest, HttpResponse.BodyHandlers.ofString());

            // Get all members and find the one we just created
            HttpRequest getAllRequest = HttpRequest.newBuilder(baseUri)
                    .header("Accept", "application/json")
                    .GET()
                    .build();

            HttpResponse<String> getAllResponse = httpClient.send(getAllRequest,
                    HttpResponse.BodyHandlers.ofString());
            JsonArray members = parseJsonArray(getAllResponse.body());

            Optional<Long> newMemberId = findMemberIdByEmail(members, uniqueEmail);
            assertTrue(newMemberId.isPresent(), "New member should exist in the list");

            idToTest = newMemberId.get();
        }

        // Test the get by ID endpoint
        URI memberUri = new URI(baseUri + "/" + idToTest);
        HttpRequest getMemberRequest = HttpRequest.newBuilder(memberUri)
                .header("Accept", "application/json")
                .GET()
                .build();

        HttpResponse<String> response = httpClient.send(getMemberRequest, HttpResponse.BodyHandlers.ofString());

        assertEquals(expectedStatus, response.statusCode(),
                "Status code should match expected for " + testDescription);

        // If we expect success, validate the response body
        if (expectedStatus == 200) {
            JsonObject member = parseJsonObject(response.body());
            assertTrue(member.containsKey("id"), "Member should have an ID");
            assertTrue(member.containsKey("name"), "Member should have a name");
            assertTrue(member.containsKey("email"), "Member should have an email");
            assertTrue(member.containsKey("phoneNumber"), "Member should have a phone number");
        }
    }

    static Stream<Object[]> getMemberByIdTestData() {
        return Stream.of(
                // We need a valid ID, but since we don't know existing IDs,
                // this will be handled specially in the test
                new Object[] { 1L, 200, "Valid member ID" },
                new Object[] { -1L, 404, "Negative member ID" },
                new Object[] { 999999L, 404, "Non-existent member ID" });
    }

    /**
     * Parse a JSON string to a JsonArray
     */
    private JsonArray parseJsonArray(String json) {
        try (JsonReader reader = Json.createReader(new StringReader(json))) {
            return reader.readArray();
        }
    }

    /**
     * Parse a JSON string to a JsonObject
     */
    private JsonObject parseJsonObject(String json) {
        try (JsonReader reader = Json.createReader(new StringReader(json))) {
            return reader.readObject();
        }
    }

    /**
     * Find a member's ID by email in a list of members
     */
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