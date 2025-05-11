package org.jboss.as.quickstarts.kitchensink.data;

import org.jboss.as.quickstarts.kitchensink.model.Member;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;

import java.util.List;
import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;

@DataJpaTest
public class MemberRepositoryTest {

    @Autowired
    private TestEntityManager entityManager;

    @Autowired
    private MemberRepository memberRepository;

    @Test
    public void testFindByEmail() {
        // given
        Member member = new Member();
        member.setName("Test User");
        member.setEmail("test@example.com");
        member.setPhoneNumber("1234567890");
        entityManager.persist(member);
        entityManager.flush();

        // when
        Optional<Member> found = memberRepository.findByEmail("test@example.com");

        // then
        assertTrue(found.isPresent());
        assertEquals("Test User", found.get().getName());
    }

    @Test
    public void testFindAllByOrderByNameAsc() {
        // given
        Member member1 = new Member();
        member1.setName("Charlie");
        member1.setEmail("charlie@example.com");
        member1.setPhoneNumber("1234567890");

        Member member2 = new Member();
        member2.setName("Alice");
        member2.setEmail("alice@example.com");
        member2.setPhoneNumber("0987654321");

        Member member3 = new Member();
        member3.setName("Bob");
        member3.setEmail("bob@example.com");
        member3.setPhoneNumber("5678901234");

        entityManager.persist(member1);
        entityManager.persist(member2);
        entityManager.persist(member3);
        entityManager.flush();

        // when
        List<Member> members = memberRepository.findAllByOrderByNameAsc();

        // then
        assertEquals(3, members.size());
        assertEquals("Alice", members.get(0).getName());
        assertEquals("Bob", members.get(1).getName());
        assertEquals("Charlie", members.get(2).getName());
    }
}