package org.jboss.as.quickstarts.kitchensink.config;

import de.flapdoodle.embed.mongo.distribution.Version;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.core.env.Environment;
import de.flapdoodle.embed.mongo.distribution.IFeatureAwareVersion;

@Configuration
public class EmbeddedMongoConfig {

    @Bean
    @Primary
    public IFeatureAwareVersion embeddedMongoVersion(Environment environment) {
        String version = environment.getProperty("de.flapdoodle.mongodb.embedded.version", "5.0.5");
        return Version.V5_0_5;
    }
}