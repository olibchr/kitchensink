package org.jboss.as.quickstarts.kitchensink.service;

import jakarta.validation.ValidationException;
import org.jboss.as.quickstarts.kitchensink.data.MemberRepository;
import org.jboss.as.quickstarts.kitchensink.model.Member;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Arrays;
import java.util.Date;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
public class MemberServiceTest {

    @Mock
    private MemberRepository memberRepository;

    @InjectMocks
    private MemberServiceImpl memberService;

    private Member testMember;

    @BeforeEach
    void setUp() {
        testMember = new Member();
        testMember.setId("60f7a6b15f8ee27e1a61dea4");
        testMember.setName("Test User");
        testMember.setEmail("test@example.com");
        testMember.setPhoneNumber("1234567890");
    }

    @Test
    void testRegisterSuccess() throws Exception {
        // given
        when(memberRepository.findByEmail(anyString())).thenReturn(Optional.empty());
        when(memberRepository.save(any(Member.class))).thenAnswer(invocation -> {
            Member savedMember = invocation.getArgument(0);
            savedMember.setId("60f7a6b15f8ee27e1a61dea4");
            savedMember.setCreatedAt(new Date());
            savedMember.setUpdatedAt(new Date());
            return savedMember;
        });

        // when
        Member registeredMember = memberService.register(testMember);

        // then
        assertNotNull(registeredMember);
        assertEquals("Test User", registeredMember.getName());
        verify(memberRepository).findByEmail("test@example.com");
        verify(memberRepository).save(testMember);
    }

    @Test
    void testRegisterWithExistingEmail() {
        // given
        when(memberRepository.findByEmail("test@example.com")).thenReturn(Optional.of(testMember));

        // when/then
        Exception exception = assertThrows(ValidationException.class, () -> {
            try {
                memberService.register(testMember);
            } catch (Exception e) {
                throw e;
            }
        });

        assertTrue(exception.getMessage().contains("Email already exists"));
        verify(memberRepository).findByEmail("test@example.com");
        verify(memberRepository, never()).save(any(Member.class));
    }

    @Test
    void testFindAllOrderedByName() {
        // given
        Member member1 = new Member();
        member1.setName("Alice");
        member1.setId("60f7a6b15f8ee27e1a61dea1");

        Member member2 = new Member();
        member2.setName("Bob");
        member2.setId("60f7a6b15f8ee27e1a61dea2");

        List<Member> expectedMembers = Arrays.asList(member1, member2);
        when(memberRepository.findAllByOrderByNameAsc()).thenReturn(expectedMembers);

        // when
        List<Member> members = memberService.findAllOrderedByName();

        // then
        assertEquals(2, members.size());
        assertEquals("Alice", members.get(0).getName());
        assertEquals("Bob", members.get(1).getName());
        verify(memberRepository).findAllByOrderByNameAsc();
    }

    @Test
    void testFindById() {
        // given
        when(memberRepository.findById("60f7a6b15f8ee27e1a61dea4")).thenReturn(Optional.of(testMember));

        // when
        Optional<Member> foundMember = memberService.findById("60f7a6b15f8ee27e1a61dea4");

        // then
        assertTrue(foundMember.isPresent());
        assertEquals("Test User", foundMember.get().getName());
        verify(memberRepository).findById("60f7a6b15f8ee27e1a61dea4");
    }
}