package org.jboss.as.quickstarts.kitchensink.data;

import org.jboss.as.quickstarts.kitchensink.model.Member;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.Mockito;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Arrays;
import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
public class MemberRepositoryTest {

    @Mock
    private MemberRepository memberRepository;

    @Test
    public void testSave() {
        // given
        Member member = new Member();
        member.setName("Test User");
        member.setEmail("test@example.com");
        member.setPhoneNumber("1234567890");

        when(memberRepository.save(any(Member.class))).thenAnswer(invocation -> {
            Member savedMember = invocation.getArgument(0);
            savedMember.setId("generatedId");
            return savedMember;
        });

        // when
        Member saved = memberRepository.save(member);

        // then
        assertNotNull(saved.getId());
        assertEquals("generatedId", saved.getId());
    }

    @Test
    public void testFindByEmail() {
        // given
        Member member = new Member();
        member.setName("Test User");
        member.setEmail("test2@example.com");
        member.setPhoneNumber("1234567890");

        when(memberRepository.findByEmail("test2@example.com")).thenReturn(Optional.of(member));

        // when
        Optional<Member> found = memberRepository.findByEmail("test2@example.com");

        // then
        assertTrue(found.isPresent());
        assertEquals("Test User", found.get().getName());
    }

    @Test
    public void testFindAllByOrderByNameAsc() {
        // given
        Member member1 = new Member();
        member1.setName("Alice");

        Member member2 = new Member();
        member2.setName("Bob");

        Member member3 = new Member();
        member3.setName("Charlie");

        when(memberRepository.findAllByOrderByNameAsc()).thenReturn(
                Arrays.asList(member1, member2, member3));

        // when
        List<Member> members = memberRepository.findAllByOrderByNameAsc();

        // then
        assertEquals(3, members.size());
        assertEquals("Alice", members.get(0).getName());
        assertEquals("Bob", members.get(1).getName());
        assertEquals("Charlie", members.get(2).getName());
    }
}