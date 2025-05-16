package org.jboss.as.quickstarts.kitchensink.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.mongodb.config.EnableMongoAuditing;
import org.springframework.data.mongodb.repository.config.EnableMongoRepositories;

@Configuration
@EnableMongoRepositories(basePackages = "org.jboss.as.quickstarts.kitchensink.data")
@EnableMongoAuditing
public class MongoConfig {

    // Additional MongoDB configuration can be added here if needed

}