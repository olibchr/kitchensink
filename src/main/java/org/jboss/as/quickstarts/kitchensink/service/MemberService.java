package org.jboss.as.quickstarts.kitchensink.service;

import org.jboss.as.quickstarts.kitchensink.model.Member;

import java.util.List;
import java.util.Optional;

public interface MemberService {

    Member register(Member member) throws Exception;

    List<Member> findAllOrderedByName();

    Optional<Member> findById(Long id);

    Optional<Member> findByEmail(String email);
}