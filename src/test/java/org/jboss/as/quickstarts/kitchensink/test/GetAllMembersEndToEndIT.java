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
import java.util.UUID;
import java.util.logging.Logger;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * End-to-end integration test for the GET /members endpoint
 */
@ExtendWith(SpringExtension.class)
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
public class GetAllMembersEndToEndIT {

    private static final Logger log = Logger.getLogger(GetAllMembersEndToEndIT.class.getName());
    private final HttpClient httpClient = HttpClient.newHttpClient();

    @LocalServerPort
    private int port;

    private URI baseUri;

    @BeforeEach
    public void setup() throws URISyntaxException {
        this.baseUri = new URI("http://localhost:" + port + "/kitchensink/rest/members");
    }

    @Test
    public void testGetAllMembers() throws Exception {
        log.info("Testing GET /members");

        // Create a test member to ensure there's at least one in the list
        String uniqueId = UUID.randomUUID().toString().substring(0, 8);
        String uniqueEmail = "test." + uniqueId + "@example.com";

        JsonObject newMemberJson = Json.createObjectBuilder()
                .add("name", "List Test Member")
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

        // Get all members
        HttpRequest getAllRequest = HttpRequest.newBuilder(baseUri)
                .header("Accept", "application/json")
                .GET()
                .build();

        HttpResponse<String> getAllResponse = httpClient.send(getAllRequest, HttpResponse.BodyHandlers.ofString());
        assertEquals(200, getAllResponse.statusCode(), "GET /members should return 200 OK");

        // Parse the response
        JsonArray members = parseJsonArray(getAllResponse.body());
        assertTrue(members.size() > 0, "Members list should not be empty");

        // Verify that our created member is in the list
        boolean foundCreatedMember = false;
        for (JsonValue value : members) {
            JsonObject member = value.asJsonObject();
            if (uniqueEmail.equals(member.getString("email"))) {
                foundCreatedMember = true;
                assertEquals("List Test Member", member.getString("name"), "Member name should match");
                assertEquals("1234567890", member.getString("phoneNumber"), "Member phone should match");
                assertTrue(member.containsKey("id"), "Member should have an ID");
                break;
            }
        }
        assertTrue(foundCreatedMember, "Created member should be in the list");
    }

    private JsonArray parseJsonArray(String json) {
        try (JsonReader reader = Json.createReader(new StringReader(json))) {
            return reader.readArray();
        }
    }
}