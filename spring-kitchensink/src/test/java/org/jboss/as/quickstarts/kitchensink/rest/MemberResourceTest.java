package org.jboss.as.quickstarts.kitchensink.rest;

import org.jboss.as.quickstarts.kitchensink.model.Member;
import org.jboss.as.quickstarts.kitchensink.service.MemberService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.web.servlet.MockMvc;

import java.util.Arrays;
import java.util.Optional;

import static org.hamcrest.Matchers.hasSize;
import static org.hamcrest.Matchers.is;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(MemberResource.class)
public class MemberResourceTest {

    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private MemberService memberService;

    @Test
    public void testListAllMembers() throws Exception {
        // given
        Member member1 = new Member();
        member1.setId(1L);
        member1.setName("Member 1");
        member1.setEmail("member1@example.com");
        member1.setPhoneNumber("1234567890");

        Member member2 = new Member();
        member2.setId(2L);
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
        member.setId(1L);
        member.setName("Test Member");
        member.setEmail("test@example.com");
        member.setPhoneNumber("1234567890");

        when(memberService.findById(1L)).thenReturn(Optional.of(member));

        // when & then
        mockMvc.perform(get("/rest/members/1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.name", is("Test Member")))
                .andExpect(jsonPath("$.email", is("test@example.com")));
    }

    @Test
    public void testGetMemberByIdNotFound() throws Exception {
        // given
        when(memberService.findById(999L)).thenReturn(Optional.empty());

        // when & then
        mockMvc.perform(get("/rest/members/999"))
                .andExpect(status().isNotFound());
    }
}