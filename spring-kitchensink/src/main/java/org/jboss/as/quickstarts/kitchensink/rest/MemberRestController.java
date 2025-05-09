package org.jboss.as.quickstarts.kitchensink.rest;

import jakarta.validation.ValidationException;
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

@RestController
@RequestMapping("/rest/members")
public class MemberRestController {

    private final MemberService memberService;

    @Autowired
    public MemberRestController(MemberService memberService) {
        this.memberService = memberService;
    }

    @GetMapping
    public List<Member> listAllMembers() {
        return memberService.findAllOrderedByName();
    }

    @GetMapping("/{id}")
    public Member getMemberById(@PathVariable("id") Long id) {
        return memberService.findById(id)
                .orElseThrow(
                        () -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Member not found with id: " + id));
    }

    @PostMapping
    public ResponseEntity<?> createMember(@RequestBody Member member) {
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