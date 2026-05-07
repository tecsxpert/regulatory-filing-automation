package com.internship.tool.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

/**
 * AiServiceClient.java
 * 
 * Communicates with the Flask AI Service (running on port 5000)
 * Handles all HTTP calls to AI endpoints with proper timeout and error handling
 * 
 * Endpoints:
 * - POST /describe - Describe a filing
 * - POST /categorise - Categorise a filing
 * - POST /generate-report - Generate regulatory report
 * - POST /query - Query with RAG (Retrieval Augmented Generation)
 * - GET /health - Health check
 * 
 * Timeout: 10 seconds
 * Error Handling: Returns null on failure (graceful degradation)
 */

@Slf4j
@Service
public class AiServiceClient {

    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;
    private final String aiServiceBaseUrl;
    
    // Constants
    private static final int TIMEOUT_SECONDS = 10;
    private static final String AI_SERVICE_URL_DEFAULT = "http://localhost:5000";
    private static final String HEALTH_ENDPOINT = "/health";
    private static final String DESCRIBE_ENDPOINT = "/describe";
    private static final String CATEGORISE_ENDPOINT = "/categorise";
    private static final String GENERATE_REPORT_ENDPOINT = "/generate-report";
    private static final String QUERY_ENDPOINT = "/query";

    /**
     * Constructor - Initializes RestTemplate with 10-second timeout
     * 
     * @param restTemplateBuilder Spring's RestTemplateBuilder for configuration
     * @param aiServiceUrl AI service base URL (injected from application.yml)
     */
    public AiServiceClient(
            RestTemplateBuilder restTemplateBuilder,
            @Value("${ai.service.url:" + AI_SERVICE_URL_DEFAULT + "}") String aiServiceUrl) {
        
        this.aiServiceBaseUrl = aiServiceUrl;
        this.objectMapper = new ObjectMapper();
        
        // Configure RestTemplate with 10-second timeout
        this.restTemplate = restTemplateBuilder
                .setConnectTimeout(Duration.ofSeconds(TIMEOUT_SECONDS))
                .setReadTimeout(Duration.ofSeconds(TIMEOUT_SECONDS))
                .build();
        
        log.info("AiServiceClient initialized with base URL: {}", aiServiceBaseUrl);
    }

    // ============================================================================
    // DESCRIBE ENDPOINT - Describe a filing
    // ============================================================================

    /**
     * Describe a filing using AI service
     * 
     * @param filingId The ID of the filing to describe
     * @param content The filing content to analyze
     * @return Map containing description and metadata, or null on error
     * 
     * Example Response:
     * {
     *   "filing_id": "123",
     *   "description": "Analysis of filing 123: Q1 Compliance Report",
     *   "status": "success"
     * }
     */
    public Map<String, Object> describe(String filingId, String content) {
        try {
            String url = aiServiceBaseUrl + DESCRIBE_ENDPOINT;
            
            // Build request payload
            Map<String, String> requestBody = new HashMap<>();
            requestBody.put("filing_id", filingId);
            requestBody.put("content", content);
            
            log.info("Calling AI service - DESCRIBE endpoint for filing: {}", filingId);
            
            // Make REST call
            Map<String, Object> response = restTemplate.postForObject(
                    url,
                    requestBody,
                    Map.class
            );
            
            log.info("DESCRIBE response received for filing: {}", filingId);
            return response;
            
        } catch (RestClientException e) {
            log.error("Error calling DESCRIBE endpoint for filing {}: {}", 
                    filingId, e.getMessage(), e);
            return null;  // Graceful null return on error
            
        } catch (Exception e) {
            log.error("Unexpected error in describe() for filing {}: {}", 
                    filingId, e.getMessage(), e);
            return null;  // Graceful null return on error
        }
    }

    // ============================================================================
    // CATEGORISE ENDPOINT - Categorise a filing
    // ============================================================================

    /**
     * Categorise a filing using AI service
     * 
     * @param content The filing content to categorise
     * @return Map containing category, confidence, and reasoning, or null on error
     * 
     * Example Response:
     * {
     *   "content": "Financial statement for...",
     *   "category": "REGULATORY",
     *   "confidence": 0.92,
     *   "status": "success"
     * }
     */
    public Map<String, Object> categorise(String content) {
        try {
            String url = aiServiceBaseUrl + CATEGORISE_ENDPOINT;
            
            // Build request payload
            Map<String, String> requestBody = new HashMap<>();
            requestBody.put("content", content);
            
            log.info("Calling AI service - CATEGORISE endpoint");
            
            // Make REST call
            Map<String, Object> response = restTemplate.postForObject(
                    url,
                    requestBody,
                    Map.class
            );
            
            log.info("CATEGORISE response received");
            return response;
            
        } catch (RestClientException e) {
            log.error("Error calling CATEGORISE endpoint: {}", e.getMessage(), e);
            return null;  // Graceful null return on error
            
        } catch (Exception e) {
            log.error("Unexpected error in categorise(): {}", e.getMessage(), e);
            return null;  // Graceful null return on error
        }
    }

    // ============================================================================
    // GENERATE-REPORT ENDPOINT - Generate regulatory report
    // ============================================================================

    /**
     * Generate a regulatory report using AI service
     * 
     * @param filingId The ID of the filing
     * @param documentType The type of document (e.g., COMPLIANCE, FINANCIAL)
     * @return Map containing generated report with title, summary, items, and recommendations, or null on error
     * 
     * Example Response:
     * {
     *   "filing_id": "123",
     *   "document_type": "COMPLIANCE",
     *   "report": {
     *     "title": "Compliance Report",
     *     "executive_summary": "...",
     *     "overview": "...",
     *     "top_items": [...],
     *     "recommendations": [...]
     *   },
     *   "status": "success"
     * }
     */
    public Map<String, Object> generateReport(String filingId, String documentType) {
        try {
            String url = aiServiceBaseUrl + GENERATE_REPORT_ENDPOINT;
            
            // Build request payload
            Map<String, String> requestBody = new HashMap<>();
            requestBody.put("filing_id", filingId);
            requestBody.put("document_type", documentType);
            
            log.info("Calling AI service - GENERATE-REPORT endpoint for filing: {}", filingId);
            
            // Make REST call (this is an expensive operation)
            Map<String, Object> response = restTemplate.postForObject(
                    url,
                    requestBody,
                    Map.class
            );
            
            log.info("GENERATE-REPORT response received for filing: {}", filingId);
            return response;
            
        } catch (RestClientException e) {
            log.error("Error calling GENERATE-REPORT endpoint for filing {}: {}", 
                    filingId, e.getMessage(), e);
            return null;  // Graceful null return on error
            
        } catch (Exception e) {
            log.error("Unexpected error in generateReport() for filing {}: {}", 
                    filingId, e.getMessage(), e);
            return null;  // Graceful null return on error
        }
    }

    // ============================================================================
    // QUERY ENDPOINT - RAG query (Retrieval Augmented Generation)
    // ============================================================================

    /**
     * Query the AI service with RAG (Retrieval Augmented Generation)
     * Retrieves relevant knowledge base chunks and uses them to answer questions
     * 
     * @param question The question to ask
     * @return Map containing answer and source documents, or null on error
     * 
     * Example Response:
     * {
     *   "question": "What are compliance requirements?",
     *   "answer": "Compliance requirements include...",
     *   "sources": [
     *     "regulatory_doc_1.txt",
     *     "regulatory_doc_2.txt"
     *   ],
     *   "status": "success"
     * }
     */
    public Map<String, Object> query(String question) {
        try {
            String url = aiServiceBaseUrl + QUERY_ENDPOINT;
            
            // Build request payload
            Map<String, String> requestBody = new HashMap<>();
            requestBody.put("question", question);
            
            log.info("Calling AI service - QUERY endpoint");
            
            // Make REST call
            Map<String, Object> response = restTemplate.postForObject(
                    url,
                    requestBody,
                    Map.class
            );
            
            log.info("QUERY response received");
            return response;
            
        } catch (RestClientException e) {
            log.error("Error calling QUERY endpoint: {}", e.getMessage(), e);
            return null;  // Graceful null return on error
            
        } catch (Exception e) {
            log.error("Unexpected error in query(): {}", e.getMessage(), e);
            return null;  // Graceful null return on error
        }
    }

    // ============================================================================
    // HEALTH CHECK ENDPOINT - Verify AI service is running
    // ============================================================================

    /**
     * Health check - Verify AI service is healthy and running
     * 
     * @return true if AI service is healthy, false otherwise
     * 
     * Example Response:
     * {
     *   "status": "healthy",
     *   "service": "AI Service",
     *   "input_sanitisation": "enabled",
     *   "rate_limiting": "enabled"
     * }
     */
    public boolean healthCheck() {
        try {
            String url = aiServiceBaseUrl + HEALTH_ENDPOINT;
            
            log.info("Calling AI service - HEALTH endpoint");
            
            // Make REST call
            Map<String, Object> response = restTemplate.getForObject(
                    url,
                    Map.class
            );
            
            if (response != null && "healthy".equals(response.get("status"))) {
                log.info("AI service health check PASSED");
                return true;
            } else {
                log.warn("AI service health check returned unhealthy status");
                return false;
            }
            
        } catch (RestClientException e) {
            log.error("Error calling HEALTH endpoint: {}", e.getMessage());
            return false;
            
        } catch (Exception e) {
            log.error("Unexpected error in healthCheck(): {}", e.getMessage(), e);
            return false;
        }
    }

    // ============================================================================
    // UTILITY METHODS
    // ============================================================================

    /**
     * Check if AI service is available
     * Used to determine if AI features should be enabled
     * 
     * @return true if service is available, false if unavailable
     */
    public boolean isAiServiceAvailable() {
        return healthCheck();
    }

    /**
     * Get the configured AI service base URL
     * 
     * @return The base URL of the AI service
     */
    public String getAiServiceUrl() {
        return aiServiceBaseUrl;
    }

    /**
     * Get the configured timeout duration
     * 
     * @return Timeout in seconds
     */
    public int getTimeoutSeconds() {
        return TIMEOUT_SECONDS;
    }

    // ============================================================================
    // ERROR HANDLING STRATEGY
    // ============================================================================

    /**
     * Error Handling Philosophy:
     * 
     * 1. TIMEOUT HANDLING (10 seconds)
     *    - Connection timeout: 10 seconds
     *    - Read timeout: 10 seconds
     *    - If exceeded: Returns null (graceful degradation)
     * 
     * 2. NETWORK ERRORS
     *    - Connection refused: Returns null
     *    - Connection timeout: Returns null
     *    - Socket exception: Returns null
     * 
     * 3. HTTP ERRORS
     *    - 400 Bad Request: Logged and returns null
     *    - 429 Rate Limited: Logged and returns null
     *    - 500 Server Error: Logged and returns null
     * 
     * 4. PARSING ERRORS
     *    - JSON parsing fails: Logged and returns null
     *    - Type mismatch: Logged and returns null
     * 
     * 5. LOGGING LEVELS
     *    - INFO: Normal requests and successful responses
     *    - WARN: Unexpected status codes
     *    - ERROR: Exceptions and failures
     * 
     * 6. GRACEFUL DEGRADATION
     *    - All errors return null instead of throwing exceptions
     *    - Allows application to continue without AI features
     *    - Frontend/Backend can detect null and show appropriate message
     *    - Application remains stable even if AI service is down
     */
}