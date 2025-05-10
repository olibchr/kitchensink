package org.jboss.as.quickstarts.kitchensink.model;

import jakarta.validation.ConstraintViolation;
import jakarta.validation.Validation;
import jakarta.validation.Validator;
import jakarta.validation.ValidatorFactory;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import java.util.Set;

import static org.junit.jupiter.api.Assertions.*;

public class MemberTest {

    private static Validator validator;

    @BeforeAll
    public static void setUp() {
        ValidatorFactory factory = Validation.buildDefaultValidatorFactory();
        validator = factory.getValidator();
    }

    @Test
    public void testValidMember() {
        Member member = new Member();
        member.setName("John Doe");
        member.setEmail("john@example.com");
        member.setPhoneNumber("1234567890");

        Set<ConstraintViolation<Member>> violations = validator.validate(member);
        assertTrue(violations.isEmpty());
    }

    @Test
    public void testInvalidEmail() {
        Member member = new Member();
        member.setName("John Doe");
        member.setEmail("not-an-email");
        member.setPhoneNumber("1234567890");

        Set<ConstraintViolation<Member>> violations = validator.validate(member);
        assertFalse(violations.isEmpty());
        assertEquals(1, violations.size());

        ConstraintViolation<Member> violation = violations.iterator().next();
        assertEquals("email", violation.getPropertyPath().toString());
    }

    @Test
    public void testNameWithNumbers() {
        Member member = new Member();
        member.setName("John123");
        member.setEmail("john@example.com");
        member.setPhoneNumber("1234567890");

        Set<ConstraintViolation<Member>> violations = validator.validate(member);
        assertFalse(violations.isEmpty());

        boolean hasNameViolation = violations.stream()
                .anyMatch(v -> v.getPropertyPath().toString().equals("name"));
        assertTrue(hasNameViolation);
    }
}