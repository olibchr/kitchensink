package org.jboss.as.quickstarts.kitchensink.service;

import jakarta.validation.ValidationException;
import org.jboss.as.quickstarts.kitchensink.data.MemberRepository;
import org.jboss.as.quickstarts.kitchensink.model.Member;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;
import java.util.logging.Logger;

@Service
public class MemberServiceImpl implements MemberService {

    private final Logger log = Logger.getLogger(MemberServiceImpl.class.getName());

    private final MemberRepository memberRepository;

    @Autowired
    public MemberServiceImpl(MemberRepository memberRepository) {
        this.memberRepository = memberRepository;
    }

    @Override
    public Member register(Member member) throws Exception {
        log.info("Registering " + member.getName());

        // Check if email is already used
        if (emailExists(member.getEmail())) {
            throw new ValidationException("Email already exists: " + member.getEmail());
        }

        return memberRepository.save(member);
    }

    @Override
    public List<Member> findAllOrderedByName() {
        return memberRepository.findAllByOrderByNameAsc();
    }

    @Override
    public Optional<Member> findById(String id) {
        return memberRepository.findById(id);
    }

    @Override
    public Optional<Member> findByEmail(String email) {
        return memberRepository.findByEmail(email);
    }

    private boolean emailExists(String email) {
        return memberRepository.findByEmail(email).isPresent();
    }
}