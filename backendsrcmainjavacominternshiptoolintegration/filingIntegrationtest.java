package com.internship.tool.integration;

import com.internship.tool.dto.FilingRequestDto;
import com.internship.tool.repository.RegulatoryFilingRepository;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.http.*;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Testcontainers
class FilingIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15")
            .withDatabaseName("tool_test")
            .withUsername("test")
            .withPassword("test");

    @Container
    static GenericContainer<?> redis = new GenericContainer<>("redis:7")
            .withExposedPorts(6379);

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
        registry.add("spring.data.redis.host", redis::getHost);
        registry.add("spring.data.redis.port", () -> redis.getMappedPort(6379));
    }

    @Autowired 
    private TestRestTemplate restTemplate;
    
    @Autowired 
    private RegulatoryFilingRepository repo;

    @Test
    void fullCrudFlow() {
        // 1. Login
        String loginBody = "{\"username\":\"admin\",\"password\":\"Admin@123\"}";
        ResponseEntity<String> loginResp = restTemplate.postForEntity(
                "/api/auth/login",
                new HttpEntity<>(loginBody, jsonHeaders()),
                String.class);
        assertThat(loginResp.getStatusCode()).isEqualTo(HttpStatus.OK);

        // 2. Create filing
        FilingRequestDto req = new FilingRequestDto();
        req.setTitle("Integration Test Filing");
        req.setStatus("PENDING");

        ResponseEntity<String> createResp = restTemplate.postForEntity(
                "/api/filings",
                new HttpEntity<>(req, jsonHeaders()),
                String.class);
        assertThat(createResp.getStatusCode()).isEqualTo(HttpStatus.CREATED);

        // 3. Verify persisted
        assertThat(repo.count()).isGreaterThan(0);
    }

    private HttpHeaders jsonHeaders() {
        HttpHeaders h = new HttpHeaders();
        h.setContentType(MediaType.APPLICATION_JSON);
        return h;
    }
}