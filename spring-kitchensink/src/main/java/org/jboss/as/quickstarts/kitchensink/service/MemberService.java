package org.jboss.as.quickstarts.kitchensink.service;

import jakarta.validation.ValidationException;
import org.jboss.as.quickstarts.kitchensink.data.MemberRepository;
import org.jboss.as.quickstarts.kitchensink.model.Member;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.logging.Logger;

@Service
public class MemberService {

    private final Logger log = Logger.getLogger(MemberService.class.getName());

    private final MemberRepository memberRepository;

    @Autowired
    public MemberService(MemberRepository memberRepository) {
        this.memberRepository = memberRepository;
    }

    @Transactional
    public Member register(Member member) {
        log.info("Registering " + member.getName());

        // Check if email is already used
        if (emailExists(member.getEmail())) {
            throw new ValidationException("Email already exists: " + member.getEmail());
        }

        return memberRepository.save(member);
    }

    public List<Member> findAllOrderedByName() {
        return memberRepository.findAllByOrderByNameAsc();
    }

    public Optional<Member> findById(Long id) {
        return memberRepository.findById(id);
    }

    public Optional<Member> findByEmail(String email) {
        return memberRepository.findByEmail(email);
    }

    private boolean emailExists(String email) {
        return memberRepository.findByEmail(email).isPresent();
    }
}