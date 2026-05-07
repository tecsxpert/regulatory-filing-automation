package com.internship.tool.entity;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import javax.persistence.*;
import java.util.Date;

import javax.persistence.Column;
import javax.persistence.Lob;
import java.util.Date;
/**
 * Filing Entity
 * 
 * Represents a regulatory filing document
 * Includes AI analysis fields for integration with Flask AI service
 * 
 * Database Table: filing
 * Timestamp fields: created_at, updated_at, report_generated_at, last_ai_analysis_at
 */

@Entity
@Table(name = "filing")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Filing {

    // ============================================================================
    // PRIMARY KEY
    // ============================================================================

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id")
    private Long id;

    // ============================================================================
    // BASIC FILING INFORMATION
    // ============================================================================

    /**
     * Title of the filing
     * Example: "Q1 Compliance Report"
     */
    @Column(name = "title", nullable = false, length = 255)
    private String title;

    /**
     * Filing description
     */
    @Column(name = "description", columnDefinition = "TEXT")
    private String description;

    /**
     * The actual content/body of the filing
     * Can be large text or document content
     */
    @Lob
    @Column(name = "content", columnDefinition = "LONGTEXT")
    private String content;

    /**
     * File type of the filing
     * Example: "PDF", "DOCX", "XLS"
     */
    @Column(name = "file_type", length = 50)
    private String fileType;

    /**
     * Filing status
     * Example: "PENDING", "APPROVED", "REJECTED"
     */
    @Column(name = "status", length = 50)
    private String status;

    /**
     * Filing reference number
     * Unique identifier for the filing
     */
    @Column(name = "reference_number", length = 100)
    private String referenceNumber;

    // ============================================================================
    // AUDIT FIELDS
    // ============================================================================

    /**
     * When the filing was created
     */
    @Column(name = "created_at")
    @Temporal(TemporalType.TIMESTAMP)
    private Date createdAt;

    /**
     * When the filing was last updated
     */
    @Column(name = "updated_at")
    @Temporal(TemporalType.TIMESTAMP)
    private Date updatedAt;

    /**
     * User ID who created the filing
     */
    @Column(name = "created_by")
    private Long createdBy;

    /**
     * User ID who last updated the filing
     */
    @Column(name = "updated_by")
    private Long updatedBy;

    // ============================================================================
    // AI SERVICE INTEGRATION FIELDS (Day 7)
    // ============================================================================

    /**
     * AI-generated description of the filing
     * Result from /describe endpoint
     * Example: "This is a quarterly compliance report..."
     */
    @Column(name = "ai_description", columnDefinition = "TEXT")
    private String aiDescription;

    /**
     * AI-categorised filing type
     * Result from /categorise endpoint
     * Example: "REGULATORY", "FINANCIAL", "COMPLIANCE"
     */
    @Column(name = "ai_category", length = 50)
    private String aiCategory;

    /**
     * Confidence score of the AI categorisation
     * Result from /categorise endpoint
     * Range: 0.0 to 1.0
     * Example: 0.92
     */
    @Column(name = "ai_confidence")
    private Double aiConfidence;

    /**
     * AI-generated regulatory report
     * Result from /generate-report endpoint
     * Stored as JSON format with title, summary, items, recommendations
     */
    @Lob
    @Column(name = "ai_report", columnDefinition = "LONGTEXT")
    private String aiReport;

    /**
     * Timestamp when the report was generated
     * Tracks when AI analysis was completed
     */
    @Column(name = "report_generated_at")
    @Temporal(TemporalType.TIMESTAMP)
    private Date reportGeneratedAt;

    /**
     * RAG (Retrieval Augmented Generation) answer
     * Result from /query endpoint
     * AI answer based on knowledge base retrieval
     */
    @Lob
    @Column(name = "rag_answer", columnDefinition = "LONGTEXT")
    private String ragAnswer;

    /**
     * Timestamp of last AI analysis
     * Tracks when most recent AI analysis occurred
     */
    @Column(name = "last_ai_analysis_at")
    @Temporal(TemporalType.TIMESTAMP)
    private Date lastAiAnalysisAt;

    /**
     * Whether AI analysis is currently in progress
     * Used to track asynchronous processing
     * Default: false
     */
    @Column(name = "ai_analysis_in_progress")
    private Boolean aiAnalysisInProgress = false;

    // ============================================================================
    // HELPER METHODS
    // ============================================================================

    /**
     * Check if filing has AI analysis results
     * 
     * @return true if AI has analyzed this filing
     */
    public boolean hasAiAnalysis() {
        return aiDescription != null || aiCategory != null || aiReport != null;
    }

    /**
     * Get AI analysis summary
     * Combines category, confidence, and description
     * 
     * @return Summary of AI findings
     */
    public String getAiAnalysisSummary() {
        StringBuilder summary = new StringBuilder();
        
        if (aiCategory != null) {
            summary.append("Category: ").append(aiCategory);
            if (aiConfidence != null) {
                summary.append(" (").append(String.format("%.0f%%", aiConfidence * 100)).append(")");
            }
            summary.append(" | ");
        }
        
        if (aiDescription != null) {
            summary.append("Description: ").append(aiDescription);
        }
        
        return summary.toString();
    }

    /**
     * Set creation timestamp
     * Called before insert
     */
    @PrePersist
    protected void onCreate() {
        createdAt = new Date();
        updatedAt = new Date();
        if (status == null) {
            status = "PENDING";
        }
    }

    /**
     * Update modification timestamp
     * Called before update
     */
    @PreUpdate
    protected void onUpdate() {
        updatedAt = new Date();
    }

    /**
     * Get display name for filing
     * 
     * @return Filing title with status
     */
    public String getDisplayName() {
        return title + " (" + status + ")";
    }

    /**
     * Check if filing is complete
     * Filing is complete if it has all required fields
     * 
     * @return true if filing has title, content, and status
     */
    public boolean isComplete() {
        return title != null && !title.isEmpty() &&
               content != null && !content.isEmpty() &&
               status != null && !status.isEmpty();
    }
    /**
     * Get AI-generated description
     */
    public String getAiDescription() {
        return aiDescription;
    }

    /**
     * Set AI-generated description
     */
    public void setAiDescription(String aiDescription) {
        this.aiDescription = aiDescription;
    }

    /**
     * Get AI-categorised filing type
     */
    public String getAiCategory() {
        return aiCategory;
    }

    /**
     * Set AI-categorised filing type
     */
    public void setAiCategory(String aiCategory) {
        this.aiCategory = aiCategory;
    }

    /**
     * Get confidence score of categorisation
     */
    public Double getAiConfidence() {
        return aiConfidence;
    }

    /**
     * Set confidence score of categorisation
     */
    public void setAiConfidence(Double aiConfidence) {
        this.aiConfidence = aiConfidence;
    }

    /**
     * Get AI-generated report
     */
    public String getAiReport() {
        return aiReport;
    }

    /**
     * Set AI-generated report
     */
    public void setAiReport(String aiReport) {
        this.aiReport = aiReport;
    }

    /**
     * Get report generation timestamp
     */
    public Date getReportGeneratedAt() {
        return reportGeneratedAt;
    }

    /**
     * Set report generation timestamp
     */
    public void setReportGeneratedAt(Date reportGeneratedAt) {
        this.reportGeneratedAt = reportGeneratedAt;
    }

    /**
     * Get RAG answer
     */
    public String getRagAnswer() {
        return ragAnswer;
    }

    /**
     * Set RAG answer
     */
    public void setRagAnswer(String ragAnswer) {
        this.ragAnswer = ragAnswer;
    }

    /**
     * Get last AI analysis timestamp
     */
    public Date getLastAiAnalysisAt() {
        return lastAiAnalysisAt;
    }

    /**
     * Set last AI analysis timestamp
     */
    public void setLastAiAnalysisAt(Date lastAiAnalysisAt) {
        this.lastAiAnalysisAt = lastAiAnalysisAt;
    }

    /**
     * Check if AI analysis is in progress
     */
    public Boolean getAiAnalysisInProgress() {
        return aiAnalysisInProgress;
    }

    /**
     * Set AI analysis in progress flag
     */
    public void setAiAnalysisInProgress(Boolean aiAnalysisInProgress) {
        this.aiAnalysisInProgress = aiAnalysisInProgress;
    } 
}

/**
 * Check if filing has AI analysis results
 * 
 * @return true if AI has analyzed this filing
 */
public boolean hasAiAnalysis() {
    return aiDescription != null || aiCategory != null || aiReport != null;
}

/**
 * Get AI analysis summary
 * 
 * @return Summary of AI findings
 */
public String getAiAnalysisSummary() {
    StringBuilder summary = new StringBuilder();
    
    if (aiCategory != null) {
        summary.append("Category: ").append(aiCategory);
        if (aiConfidence != null) {
            summary.append(" (").append(String.format("%.0f%%", aiConfidence * 100)).append(")");
        }
        summary.append(" | ");
    }
    
    if (aiDescription != null) {
        summary.append("Description: ").append(aiDescription);
    }
    
    return summary.toString();
}
