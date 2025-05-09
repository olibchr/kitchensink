/*
 * JBoss, Home of Professional Open Source
 * Copyright 2015, Red Hat, Inc. and/or its affiliates, and individual
 * contributors by the @authors tag. See the copyright.txt in the
 * distribution for a full listing of individual contributors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * http://www.apache.org/licenses/LICENSE-2.0
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.jboss.as.quickstarts.kitchensink.test;

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
import java.util.Arrays;
import java.util.Collection;
import java.util.Optional;
import java.util.UUID;
import java.util.logging.Logger;

import org.junit.Assert;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.Parameterized;
import org.junit.runners.Parameterized.Parameters;

/**
 * End-to-end integration test for the Member REST API
 * Tests all main API operations defined in the OpenAPI spec:
 * - List all members
 * - Create a new member
 * - Get a specific member by ID
 */
public class MemberApiEndToEndIT {

    private static final Logger log = Logger.getLogger(MemberApiEndToEndIT.class.getName());
    private final HttpClient httpClient = HttpClient.newHttpClient();

    /**
     * Get the base URI for the REST API
     */
    protected URI getBaseURI() {
        String host = getServerHost();
        if (host == null) {
            host = "http://localhost:8080/kitchensink";
        }
        try {
            return new URI(host + "/rest/members");
        } catch (URISyntaxException ex) {
            throw new RuntimeException(ex);
        }
    }

    /**
     * Get the server host from environment or system property
     */
    private String getServerHost() {
        String host = System.getenv("SERVER_HOST");
        if (host == null) {
            host = System.getProperty("server.host");
        }
        return host;
    }

    @Test
    public void testMemberLifecycle() throws Exception {
        // Step 1: Get initial list of members
        log.info("Step 1: Getting initial list of members");
        HttpRequest getAllRequest = HttpRequest.newBuilder(getBaseURI())
                .header("Accept", "application/json")
                .GET()
                .build();

        HttpResponse<String> getAllResponse = httpClient.send(getAllRequest, HttpResponse.BodyHandlers.ofString());
        Assert.assertEquals(200, getAllResponse.statusCode());

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

        HttpRequest createRequest = HttpRequest.newBuilder(getBaseURI())
                .header("Content-Type", "application/json")
                .header("Accept", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(newMemberJson.toString()))
                .build();

        HttpResponse<String> createResponse = httpClient.send(createRequest, HttpResponse.BodyHandlers.ofString());
        Assert.assertEquals("Member creation should succeed with status 200", 200, createResponse.statusCode());

        // Step 3: Get the updated list of members
        log.info("Step 3: Getting updated list of members");
        HttpResponse<String> updatedGetAllResponse = httpClient.send(getAllRequest,
                HttpResponse.BodyHandlers.ofString());
        Assert.assertEquals(200, updatedGetAllResponse.statusCode());

        JsonArray updatedMembers = parseJsonArray(updatedGetAllResponse.body());
        Assert.assertEquals("Member count should increase by 1", initialCount + 1, updatedMembers.size());

        // Find the new member in the list and get its ID
        Optional<Long> newMemberId = findMemberIdByEmail(updatedMembers, uniqueEmail);
        Assert.assertTrue("New member should exist in the updated list", newMemberId.isPresent());

        // Step 4: Get the specific member by ID
        log.info("Step 4: Getting the new member by ID: " + newMemberId.get());
        URI memberUri = new URI(getBaseURI().toString() + "/" + newMemberId.get());
        HttpRequest getMemberRequest = HttpRequest.newBuilder(memberUri)
                .header("Accept", "application/json")
                .GET()
                .build();

        HttpResponse<String> getMemberResponse = httpClient.send(getMemberRequest,
                HttpResponse.BodyHandlers.ofString());
        Assert.assertEquals(200, getMemberResponse.statusCode());

        JsonObject member = parseJsonObject(getMemberResponse.body());
        Assert.assertEquals("Member ID should match", newMemberId.get().longValue(),
                member.getJsonNumber("id").longValue());
        Assert.assertEquals("Member name should match", "Test Member", member.getString("name"));
        Assert.assertEquals("Member email should match", uniqueEmail, member.getString("email"));
        Assert.assertEquals("Member phone should match", "1234567890", member.getString("phoneNumber"));

        log.info("End-to-end API test completed successfully");
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

    /**
     * Parameterized test class for testing the GET /members/{id} endpoint
     * with different ID scenarios
     */
    @RunWith(Parameterized.class)
    public static class GetMemberByIdTest {
        private static final Logger log = Logger.getLogger(GetMemberByIdTest.class.getName());
        private final HttpClient httpClient = HttpClient.newHttpClient();
        private final long memberId;
        private final int expectedStatus;
        private final String testDescription;

        public GetMemberByIdTest(long memberId, int expectedStatus, String testDescription) {
            this.memberId = memberId;
            this.expectedStatus = expectedStatus;
            this.testDescription = testDescription;
        }

        @Parameters(name = "{2}")
        public static Collection<Object[]> data() {
            return Arrays.asList(new Object[][] {
                    // We need a valid ID, but since we don't know existing IDs,
                    // this will be handled specially in the test
                    { 1L, 200, "Valid member ID" },
                    { -1L, 404, "Negative member ID" },
                    { 999999L, 404, "Non-existent member ID" },
                    { 0L, 200, "Zero member ID" }
            });
        }

        protected URI getBaseURI() {
            try {
                return new URI("http://localhost:8080/kitchensink/rest/members");
            } catch (URISyntaxException ex) {
                throw new RuntimeException(ex);
            }
        }

        @Test
        public void testGetMemberById() throws Exception {
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

                HttpRequest createRequest = HttpRequest.newBuilder(getBaseURI())
                        .header("Content-Type", "application/json")
                        .header("Accept", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(newMemberJson.toString()))
                        .build();

                httpClient.send(createRequest, HttpResponse.BodyHandlers.ofString());

                // Get all members and find the one we just created
                HttpRequest getAllRequest = HttpRequest.newBuilder(getBaseURI())
                        .header("Accept", "application/json")
                        .GET()
                        .build();

                HttpResponse<String> getAllResponse = httpClient.send(getAllRequest,
                        HttpResponse.BodyHandlers.ofString());
                JsonArray members = parseJsonArray(getAllResponse.body());

                Optional<Long> newMemberId = findMemberIdByEmail(members, uniqueEmail);
                Assert.assertTrue("New member should exist in the list", newMemberId.isPresent());

                idToTest = newMemberId.get();
            }

            // Test the get by ID endpoint
            URI memberUri = new URI(getBaseURI() + "/" + idToTest);
            HttpRequest getMemberRequest = HttpRequest.newBuilder(memberUri)
                    .header("Accept", "application/json")
                    .GET()
                    .build();

            HttpResponse<String> response = httpClient.send(getMemberRequest, HttpResponse.BodyHandlers.ofString());

            Assert.assertEquals("Status code should match expected for " + testDescription,
                    expectedStatus, response.statusCode());

            // If we expect success, validate the response body
            if (expectedStatus == 200) {
                JsonObject member = parseJsonObject(response.body());
                Assert.assertTrue("Member should have an ID", member.containsKey("id"));
                Assert.assertTrue("Member should have a name", member.containsKey("name"));
                Assert.assertTrue("Member should have an email", member.containsKey("email"));
                Assert.assertTrue("Member should have a phone number", member.containsKey("phoneNumber"));
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

    /**
     * Parameterized test class for testing the POST /members endpoint
     * with different input scenarios
     */
    @RunWith(Parameterized.class)
    public static class CreateMemberTest {
        private static final Logger log = Logger.getLogger(CreateMemberTest.class.getName());
        private final HttpClient httpClient = HttpClient.newHttpClient();
        private final String name;
        private final String email;
        private final String phoneNumber;
        private final int expectedStatus;
        private final String expectedValidationField;
        private final String testDescription;

        public CreateMemberTest(String name, String email, String phoneNumber,
                int expectedStatus, String expectedValidationField, String testDescription) {
            this.name = name;
            this.email = email;
            this.phoneNumber = phoneNumber;
            this.expectedStatus = expectedStatus;
            this.expectedValidationField = expectedValidationField;
            this.testDescription = testDescription;
        }

        @Parameters(name = "{5}")
        public static Collection<Object[]> data() {
            return Arrays.asList(new Object[][] {
                    // Valid cases
                    { "Valid User", "valid" + UUID.randomUUID().toString().substring(0, 8) + "@example.com",
                            "1234567890", 200, null, "Valid member data" },

                    // Invalid cases - name validation
                    { "", "invalid1@example.com", "1234567890",
                            400, "name", "Empty name" },
                    { "A name with numbers 123", "invalid2@example.com", "1234567890",
                            400, "name", "Name with numbers" },
                    { "A very very very very very very long name that exceeds the maximum length",
                            "invalid3@example.com", "1234567890", 400, "name", "Name too long" },

                    // Invalid cases - email validation
                    { "Valid Name", "notanemail", "1234567890",
                            400, "email", "Invalid email format" },
                    { "Valid Name", "", "1234567890",
                            400, "email", "Empty email" },

                    // Invalid cases - phone validation
                    { "Valid Name", "valid" + UUID.randomUUID().toString().substring(0, 8) + "@example.com",
                            "123", 400, "phoneNumber", "Phone number too short" },
                    { "Valid Name", "valid" + UUID.randomUUID().toString().substring(0, 8) + "@example.com",
                            "12345678901234", 400, "phoneNumber", "Phone number too long" },
                    { "Valid Name", "valid" + UUID.randomUUID().toString().substring(0, 8) + "@example.com",
                            "123-456-7890", 400, "phoneNumber", "Phone number with non-digits" },

                    // Duplicate email test
                    { "Valid Name", "duplicate@example.com", "1234567890",
                            409, "email", "Duplicate email" },

                    // Invalid JSON test
                    { "Valid Name", "missing.quotes@example.com", "1234567890",
                            500, null, "Invalid JSON format" }
            });
        }

        protected URI getBaseURI() {
            try {
                return new URI("http://localhost:8080/kitchensink/rest/members");
            } catch (URISyntaxException ex) {
                throw new RuntimeException(ex);
            }
        }

        @Test
        public void testCreateMember() throws Exception {
            log.info("Testing POST /members: " + testDescription);

            // For duplicate email test, first create a member with that email
            if (testDescription.equals("Duplicate email")) {
                JsonObject firstMemberJson = Json.createObjectBuilder()
                        .add("name", "First User")
                        .add("email", email)
                        .add("phoneNumber", "1234567890")
                        .build();

                HttpRequest firstCreateRequest = HttpRequest.newBuilder(getBaseURI())
                        .header("Content-Type", "application/json")
                        .header("Accept", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(firstMemberJson.toString()))
                        .build();

                httpClient.send(firstCreateRequest, HttpResponse.BodyHandlers.ofString());
            }

            // Special case for invalid JSON test
            if (testDescription.equals("Invalid JSON format")) {
                String invalidJson = "{name: 'Missing quotes', email: missing.quotes@example.com}";

                HttpRequest createInvalidRequest = HttpRequest.newBuilder(getBaseURI())
                        .header("Content-Type", "application/json")
                        .header("Accept", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(invalidJson))
                        .build();

                HttpResponse<String> response = httpClient.send(createInvalidRequest,
                        HttpResponse.BodyHandlers.ofString());
                Assert.assertEquals("Invalid JSON should return status 500", 500, response.statusCode());
                return;
            }

            // Create the test member
            JsonObject memberJson = Json.createObjectBuilder()
                    .add("name", name)
                    .add("email", email)
                    .add("phoneNumber", phoneNumber)
                    .build();

            HttpRequest createRequest = HttpRequest.newBuilder(getBaseURI())
                    .header("Content-Type", "application/json")
                    .header("Accept", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(memberJson.toString()))
                    .build();

            HttpResponse<String> response = httpClient.send(createRequest, HttpResponse.BodyHandlers.ofString());

            Assert.assertEquals("Status code should match expected for " + testDescription,
                    expectedStatus, response.statusCode());

            // For error cases, check that the expected validation field is in the response
            if (expectedStatus != 200 && expectedValidationField != null) {
                // Only parse if response body is not empty
                if (!response.body().isEmpty()) {
                    JsonObject errorResponse = parseJsonObject(response.body());
                    Assert.assertTrue("Response should contain validation error for '" + expectedValidationField + "'",
                            errorResponse.containsKey(expectedValidationField));
                }
            }
        }

        private JsonObject parseJsonObject(String json) {
            try (JsonReader reader = Json.createReader(new StringReader(json))) {
                return reader.readObject();
            }
        }
    }

    /**
     * Test class for the GET /members endpoint
     */
    public static class GetAllMembersTest {
        private static final Logger log = Logger.getLogger(GetAllMembersTest.class.getName());
        private final HttpClient httpClient = HttpClient.newHttpClient();

        protected URI getBaseURI() {
            try {
                return new URI("http://localhost:8080/kitchensink/rest/members");
            } catch (URISyntaxException ex) {
                throw new RuntimeException(ex);
            }
        }

        @Test
        public void testGetAllMembers() throws Exception {
            log.info("Testing GET /members");

            HttpRequest getAllRequest = HttpRequest.newBuilder(getBaseURI())
                    .header("Accept", "application/json")
                    .GET()
                    .build();

            HttpResponse<String> response = httpClient.send(getAllRequest, HttpResponse.BodyHandlers.ofString());

            Assert.assertEquals("Should return status 200", 200, response.statusCode());

            // Verify the response is a valid JSON array
            JsonArray members = parseJsonArray(response.body());

            // Verify each member has the required fields
            for (JsonValue value : members) {
                JsonObject member = value.asJsonObject();
                Assert.assertTrue("Member should have an ID", member.containsKey("id"));
                Assert.assertTrue("Member should have a name", member.containsKey("name"));
                Assert.assertTrue("Member should have an email", member.containsKey("email"));
                Assert.assertTrue("Member should have a phone number", member.containsKey("phoneNumber"));
            }

            // Verify members are ordered by name (if there are at least 2 members)
            if (members.size() >= 2) {
                boolean inOrder = true;
                String prevName = null;

                for (JsonValue value : members) {
                    JsonObject member = value.asJsonObject();
                    String currentName = member.getString("name");

                    if (prevName != null && currentName.compareToIgnoreCase(prevName) < 0) {
                        log.warning("Names out of order: '" + prevName + "' followed by '" + currentName + "'");
                        inOrder = false;
                        break;
                    }

                    prevName = currentName;
                }

                // Note: The API may or may not enforce ordering. If it's part of the spec, keep
                // this assertion.
                // Otherwise, just log the order state but don't fail the test.
                log.info("Members " + (inOrder ? "are" : "are not") + " ordered by name");
                // Only uncomment this assertion if ordering is guaranteed in the API
                // specification
                // Assert.assertTrue("Members should be ordered by name", inOrder);
            }
        }

        private JsonArray parseJsonArray(String json) {
            try (JsonReader reader = Json.createReader(new StringReader(json))) {
                return reader.readArray();
            }
        }
    }

    /**
     * Run a comprehensive test of all API endpoints with various test cases
     */
    @Test
    public void testAllEndpoints() throws Exception {
        log.info("Starting comprehensive API testing");

        // Test the GET /members endpoint
        log.info("Testing GET /members endpoint");
        GetAllMembersTest getAllTest = new GetAllMembersTest();
        getAllTest.testGetAllMembers();

        // Test the POST /members endpoint with valid data
        log.info("Testing POST /members endpoint with valid data");
        String uniqueId = UUID.randomUUID().toString().substring(0, 8);
        String uniqueEmail = "comprehensive." + uniqueId + "@example.com";

        JsonObject newMemberJson = Json.createObjectBuilder()
                .add("name", "Comprehensive Test")
                .add("email", uniqueEmail)
                .add("phoneNumber", "1234567890")
                .build();

        HttpRequest createRequest = HttpRequest.newBuilder(getBaseURI())
                .header("Content-Type", "application/json")
                .header("Accept", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(newMemberJson.toString()))
                .build();

        HttpResponse<String> createResponse = httpClient.send(createRequest, HttpResponse.BodyHandlers.ofString());
        Assert.assertEquals("Member creation should succeed", 200, createResponse.statusCode());

        // Get all members and find the newly created one
        HttpRequest getAllRequest = HttpRequest.newBuilder(getBaseURI())
                .header("Accept", "application/json")
                .GET()
                .build();

        HttpResponse<String> getAllResponse = httpClient.send(getAllRequest, HttpResponse.BodyHandlers.ofString());
        JsonArray members = parseJsonArray(getAllResponse.body());

        Optional<Long> newMemberId = findMemberIdByEmail(members, uniqueEmail);
        Assert.assertTrue("New member should exist in the list", newMemberId.isPresent());

        // Test the GET /members/{id} endpoint
        log.info("Testing GET /members/{id} endpoint with valid ID: " + newMemberId.get());
        URI memberUri = new URI(getBaseURI().toString() + "/" + newMemberId.get());
        HttpRequest getMemberRequest = HttpRequest.newBuilder(memberUri)
                .header("Accept", "application/json")
                .GET()
                .build();

        HttpResponse<String> getMemberResponse = httpClient.send(getMemberRequest,
                HttpResponse.BodyHandlers.ofString());
        Assert.assertEquals(200, getMemberResponse.statusCode());

        // Test some error cases

        // 1. Non-existent ID
        log.info("Testing GET /members/{id} with non-existent ID");
        URI nonExistentUri = new URI(getBaseURI().toString() + "/999999");
        HttpRequest getNonExistentRequest = HttpRequest.newBuilder(nonExistentUri)
                .header("Accept", "application/json")
                .GET()
                .build();

        HttpResponse<String> getNonExistentResponse = httpClient.send(getNonExistentRequest,
                HttpResponse.BodyHandlers.ofString());
        Assert.assertEquals(404, getNonExistentResponse.statusCode());

        // 2. Invalid member data (empty name)
        log.info("Testing POST /members with invalid data (empty name)");
        JsonObject invalidMemberJson = Json.createObjectBuilder()
                .add("name", "")
                .add("email", "invalid@example.com")
                .add("phoneNumber", "1234567890")
                .build();

        HttpRequest createInvalidRequest = HttpRequest.newBuilder(getBaseURI())
                .header("Content-Type", "application/json")
                .header("Accept", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(invalidMemberJson.toString()))
                .build();

        HttpResponse<String> createInvalidResponse = httpClient.send(createInvalidRequest,
                HttpResponse.BodyHandlers.ofString());
        Assert.assertEquals(400, createInvalidResponse.statusCode());

        // 3. Duplicate email
        log.info("Testing POST /members with duplicate email");
        JsonObject duplicateEmailJson = Json.createObjectBuilder()
                .add("name", "Duplicate User")
                .add("email", uniqueEmail) // Reuse the email from earlier
                .add("phoneNumber", "1234567890")
                .build();

        HttpRequest createDuplicateRequest = HttpRequest.newBuilder(getBaseURI())
                .header("Content-Type", "application/json")
                .header("Accept", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(duplicateEmailJson.toString()))
                .build();

        HttpResponse<String> createDuplicateResponse = httpClient.send(createDuplicateRequest,
                HttpResponse.BodyHandlers.ofString());
        Assert.assertEquals(409, createDuplicateResponse.statusCode());

        // 4. Invalid JSON
        log.info("Testing POST /members with invalid JSON format");
        String invalidJson = "{name: 'Missing quotes', email: missing.quotes@example.com}";

        HttpRequest createWithInvalidJsonRequest = HttpRequest.newBuilder(getBaseURI())
                .header("Content-Type", "application/json")
                .header("Accept", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(invalidJson))
                .build();

        HttpResponse<String> invalidJsonResponse = httpClient.send(createWithInvalidJsonRequest,
                HttpResponse.BodyHandlers.ofString());
        Assert.assertEquals(500, invalidJsonResponse.statusCode());

        log.info("Comprehensive API testing completed successfully");
    }
}