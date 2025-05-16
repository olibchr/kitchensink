package org.jboss.as.quickstarts.kitchensink.rest;

import jakarta.validation.Valid;
import jakarta.validation.ValidationException;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.Validator;
import org.jboss.as.quickstarts.kitchensink.model.Member;
import org.jboss.as.quickstarts.kitchensink.service.MemberService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

@RestController
@RequestMapping("/rest/members")
public class MemberRestController {

    private final MemberService memberService;
    private final Validator validator;

    @Autowired
    public MemberRestController(MemberService memberService, Validator validator) {
        this.memberService = memberService;
        this.validator = validator;
    }

    @GetMapping
    public List<Member> listAllMembers() {
        return memberService.findAllOrderedByName();
    }

    @GetMapping("/{id}")
    public Member getMemberById(@PathVariable("id") String id) {
        return memberService.findById(id)
                .orElseThrow(
                        () -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Member not found with id: " + id));
    }

    @PostMapping
    public ResponseEntity<?> createMember(@RequestBody Member member) {
        // Validate member manually
        Set<ConstraintViolation<Member>> violations = validator.validate(member);

        if (!violations.isEmpty()) {
            Map<String, String> errors = new HashMap<>();

            for (ConstraintViolation<Member> violation : violations) {
                String propertyPath = violation.getPropertyPath().toString();
                String message = violation.getMessage();
                errors.put(propertyPath, message);
            }

            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errors);
        }

        try {
            Member registeredMember = memberService.register(member);
            return ResponseEntity.ok(registeredMember);
        } catch (ValidationException e) {
            // Handle the unique constraint violation
            Map<String, String> responseObj = new HashMap<>();
            responseObj.put("email", "Email already exists");
            return ResponseEntity.status(HttpStatus.CONFLICT).body(responseObj);
        } catch (Exception e) {
            // Handle generic exceptions
            Map<String, String> responseObj = new HashMap<>();
            responseObj.put("error", e.getMessage());
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(responseObj);
        }
    }
}