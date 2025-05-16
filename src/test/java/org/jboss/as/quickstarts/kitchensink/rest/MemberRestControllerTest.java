package org.jboss.as.quickstarts.kitchensink.rest;

import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.ValidationException;
import jakarta.validation.Validator;
import org.jboss.as.quickstarts.kitchensink.model.Member;
import org.jboss.as.quickstarts.kitchensink.service.MemberService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.Arrays;
import java.util.Date;
import java.util.HashSet;
import java.util.Optional;
import java.util.Set;

import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.is;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anySet;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

public class MemberRestControllerTest {

    private MockMvc mockMvc;

    @Mock
    private MemberService memberService;

    @Mock
    private Validator validator;

    @InjectMocks
    private MemberRestController memberRestController;

    private ObjectMapper objectMapper = new ObjectMapper();

    @BeforeEach
    public void setup() {
        MockitoAnnotations.openMocks(this);
        mockMvc = MockMvcBuilders.standaloneSetup(memberRestController).build();

        // Setup validator to return empty violations by default (valid)
        when(validator.validate(any(), any())).thenReturn(new HashSet<>());
    }

    @Test
    public void testListAllMembers() throws Exception {
        // given
        Member member1 = new Member();
        member1.setId("60f7a6b15f8ee27e1a61dea1");
        member1.setName("Member 1");
        member1.setEmail("member1@example.com");
        member1.setPhoneNumber("1234567890");

        Member member2 = new Member();
        member2.setId("60f7a6b15f8ee27e1a61dea2");
        member2.setName("Member 2");
        member2.setEmail("member2@example.com");
        member2.setPhoneNumber("0987654321");

        when(memberService.findAllOrderedByName()).thenReturn(Arrays.asList(member1, member2));

        // when & then
        mockMvc.perform(get("/rest/members"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(2)))
                .andExpect(jsonPath("$[0].name", is("Member 1")))
                .andExpect(jsonPath("$[1].name", is("Member 2")));
    }

    @Test
    public void testGetMemberById() throws Exception {
        // given
        Member member = new Member();
        member.setId("60f7a6b15f8ee27e1a61dea1");
        member.setName("Test Member");
        member.setEmail("test@example.com");
        member.setPhoneNumber("1234567890");

        when(memberService.findById("60f7a6b15f8ee27e1a61dea1")).thenReturn(Optional.of(member));

        // when & then
        mockMvc.perform(get("/rest/members/60f7a6b15f8ee27e1a61dea1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name", is("Test Member")))
                .andExpect(jsonPath("$.email", is("test@example.com")));
    }

    @Test
    public void testCreateMember() throws Exception {
        // given
        Member newMember = new Member();
        newMember.setName("New Member");
        newMember.setEmail("new@example.com");
        newMember.setPhoneNumber("1234567890");

        Member savedMember = new Member();
        savedMember.setId("60f7a6b15f8ee27e1a61dea3");
        savedMember.setName("New Member");
        savedMember.setEmail("new@example.com");
        savedMember.setPhoneNumber("1234567890");

        // Set audit fields using setters for testing
        savedMember.setCreatedAt(new Date());
        savedMember.setUpdatedAt(new Date());

        // Mock validation to return no violations (valid)
        when(validator.validate(any(Member.class))).thenReturn(new HashSet<>());
        when(memberService.register(any(Member.class))).thenReturn(savedMember);

        // when & then
        mockMvc.perform(post("/rest/members")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(newMember)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id", is("60f7a6b15f8ee27e1a61dea3")))
                .andExpect(jsonPath("$.name", is("New Member")));
    }

    @Test
    public void testCreateMemberWithExistingEmail() throws Exception {
        // given
        Member newMember = new Member();
        newMember.setName("New Member");
        newMember.setEmail("existing@example.com");
        newMember.setPhoneNumber("1234567890");

        // Mock validation to return no violations (valid)
        when(validator.validate(any(Member.class))).thenReturn(new HashSet<>());
        when(memberService.register(any(Member.class))).thenThrow(new ValidationException("Email already exists"));

        // when & then
        mockMvc.perform(post("/rest/members")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(newMember)))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.email", is("Email already exists")));
    }
} 