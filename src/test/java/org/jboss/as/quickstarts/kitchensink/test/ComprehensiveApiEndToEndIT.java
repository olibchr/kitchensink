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
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.logging.Logger;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * A comprehensive end-to-end integration test for the REST API
 * This test creates multiple member records with unique data, then tests
 * retrieval with different operations. It's designed to test multiple API
 * endpoints in a real-world scenario with a larger data set.
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

    // Store member data for test validation
    static class TestMemberData {
            String id;
            String name;
            String email;
            String phone;

            TestMemberData(String name, String email, String phone) {
                    this.name = name;
                    this.email = email;
                    this.phone = phone;
            }
    }

    @BeforeEach
    public void setup() throws URISyntaxException {
        this.baseUri = new URI("http://localhost:" + port + "/kitchensink/rest/members");
    }

    @Test
    public void testComprehensiveApiFlow() throws Exception {
            // Create multiple test members and store their data
            List<TestMemberData> testMembers = new ArrayList<>();
            int numberOfTestMembers = 5;

        for (int i = 0; i < numberOfTestMembers; i++) {
                String uniqueId = UUID.randomUUID().toString().substring(0, 8);
            String name = "User " + (char) ('A' + i); // Names like User A, User B, etc.
            String email = "user." + uniqueId + "@example.com";
            String phone = "12345" + i + i + i + i + i;

            TestMemberData memberData = new TestMemberData(name, email, phone);
            testMembers.add(memberData);

            // Create the member
            JsonObject memberJson = Json.createObjectBuilder()
                            .add("name", memberData.name)
                            .add("email", memberData.email)
                            .add("phoneNumber", memberData.phone)
                            .build();

            HttpRequest createRequest = HttpRequest.newBuilder(baseUri)
                            .header("Content-Type", "application/json")
                            .header("Accept", "application/json")
                            .POST(HttpRequest.BodyPublishers.ofString(memberJson.toString()))
                            .build();

            HttpResponse<String> createResponse = httpClient.send(createRequest, HttpResponse.BodyHandlers.ofString());
            assertEquals(200, createResponse.statusCode(), "Member creation should succeed");
    }

        // Test GET all members
        HttpRequest getAllRequest = HttpRequest.newBuilder(baseUri)
                .header("Accept", "application/json")
                .GET()
                .build();

        HttpResponse<String> getAllResponse = httpClient.send(getAllRequest, HttpResponse.BodyHandlers.ofString());
        assertEquals(200, getAllResponse.statusCode(), "GET all should return 200");

        JsonArray members = parseJsonArray(getAllResponse.body());
        log.info("Retrieved " + members.size() + " members from GET /members");

        // Match IDs for our test members from the API response
        for (TestMemberData testMember : testMembers) {
                Optional<String> id = findMemberIdByEmail(members, testMember.email);
                assertTrue(id.isPresent(), "Member with email " + testMember.email + " should be present");
                testMember.id = id.get();
        }

        // Test GET member by ID for each test member
        for (TestMemberData testMember : testMembers) {
                URI memberUri = new URI(baseUri.toString() + "/" + testMember.id);
                HttpRequest getMemberRequest = HttpRequest.newBuilder(memberUri)
                                .header("Accept", "application/json")
                                .GET()
                                .build();

            HttpResponse<String> getMemberResponse = httpClient.send(getMemberRequest,
                            HttpResponse.BodyHandlers.ofString());
            assertEquals(200, getMemberResponse.statusCode(), "GET by ID should return 200");

            JsonObject member = parseJsonObject(getMemberResponse.body());
            assertEquals(testMember.id, member.getString("id"), "ID should match");
            assertEquals(testMember.name, member.getString("name"), "Name should match");
            assertEquals(testMember.email, member.getString("email"), "Email should match");
            assertEquals(testMember.phone, member.getString("phoneNumber"), "Phone should match");

            log.info("Successfully verified member: " + testMember.name);
    }

    // Test GET with a non-existent ID
    URI nonExistentUri = new URI(baseUri.toString() + "/nonexistent");
        HttpRequest getNonExistentRequest = HttpRequest.newBuilder(nonExistentUri)
                .header("Accept", "application/json")
                .GET()
                .build();

        HttpResponse<String> getNonExistentResponse = httpClient.send(getNonExistentRequest,
                HttpResponse.BodyHandlers.ofString());
        assertEquals(404, getNonExistentResponse.statusCode(), "GET with non-existent ID should return 404");

        log.info("Comprehensive API test completed successfully");
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
    private Optional<String> findMemberIdByEmail(JsonArray members, String email) {
        for (JsonValue value : members) {
            JsonObject member = value.asJsonObject();
            if (email.equals(member.getString("email"))) {
                    return Optional.of(member.getString("id"));
            }
        }
        return Optional.empty();
    }
}