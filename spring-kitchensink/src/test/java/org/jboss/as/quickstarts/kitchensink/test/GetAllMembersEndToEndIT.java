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
import java.util.logging.Logger;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Test class for the GET /members endpoint
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

        HttpRequest getAllRequest = HttpRequest.newBuilder(baseUri)
                .header("Accept", "application/json")
                .GET()
                .build();

        HttpResponse<String> response = httpClient.send(getAllRequest, HttpResponse.BodyHandlers.ofString());

        assertEquals(200, response.statusCode(), "Should return status 200");

        // Verify the response is a valid JSON array
        JsonArray members = parseJsonArray(response.body());

        // Verify each member has the required fields
        for (JsonValue value : members) {
            JsonObject member = value.asJsonObject();
            assertTrue(member.containsKey("id"), "Member should have an ID");
            assertTrue(member.containsKey("name"), "Member should have a name");
            assertTrue(member.containsKey("email"), "Member should have an email");
            assertTrue(member.containsKey("phoneNumber"), "Member should have a phone number");
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

            log.info("Members " + (inOrder ? "are" : "are not") + " ordered by name");
            // Check that members are ordered by name, which is required by the
            // MemberRestController
            assertTrue(inOrder, "Members should be ordered by name");
        }
    }

    private JsonArray parseJsonArray(String json) {
        try (JsonReader reader = Json.createReader(new StringReader(json))) {
            return reader.readArray();
        }
    }
}