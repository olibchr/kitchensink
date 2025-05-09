# Data Models

This document provides a visual representation of the data models used in the Kitchensink application.

## Member Entity

```mermaid
classDiagram
    class Member {
        +Long id
        +String name
        +String email
        +String phoneNumber
        +getId() Long
        +setId(Long id) void
        +getName() String
        +setName(String name) void
        +getEmail() String
        +setEmail(String email) void
        +getPhoneNumber() String
        +setPhoneNumber(String phoneNumber) void
    }
    
    note for Member "Annotations\n@Entity\n@XmlRootElement\n@Table(uniqueConstraints=@UniqueConstraint(columnNames='email'))"
    
    note for Member::id "@Id\n@GeneratedValue"
    note for Member::name "@NotNull\n@Size(min=1, max=25)\n@Pattern(regexp='[^0-9]*', message='Must not contain numbers')"
    note for Member::email "@NotNull\n@NotEmpty\n@Email"
    note for Member::phoneNumber "@NotNull\n@Size(min=10, max=12)\n@Digits(fraction=0, integer=12)\n@Column(name='phone_number')"
```

## Database Schema

```mermaid
erDiagram
    MEMBER {
        bigint id PK
        varchar(25) name
        varchar(255) email UK
        varchar(12) phone_number
    }
```

## Repository Relationships

```mermaid
classDiagram
    class Member {
        +Long id
        +String name
        +String email
        +String phoneNumber
    }
    
    class MemberRepository {
        -EntityManager em
        +findById(Long id) Member
        +findByEmail(String email) Member
        +findAllOrderedByName() List~Member~
    }
    
    class MemberListProducer {
        -MemberRepository memberRepository
        -List~Member~ members
        +getMembers() List~Member~
        +onMemberListChanged(Member member) void
        +retrieveAllMembersOrderedByName() void
    }
    
    class MemberResourceRESTService {
        -MemberRepository repository
        -MemberRegistration registration
        +listAllMembers() List~Member~
        +lookupMemberById(long id) Member
        +createMember(Member member) Response
    }
    
    MemberRepository --> Member : manages
    MemberListProducer --> MemberRepository : uses
    MemberListProducer --> Member : produces list of
    MemberResourceRESTService --> MemberRepository : uses
    MemberResourceRESTService --> Member : manages via REST
``` 