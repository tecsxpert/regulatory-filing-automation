package com.internship.tool.dto;

import lombok.Builder;
import lombok.Data;
import java.util.Map;

@Data
@Builder
public class StatsDto {
    private long totalFilings;
    private long pendingCount;
    private long submittedCount;
    private long approvedCount;
    private long overdueCount;
    private Map<String, Long> byCategory;
    private Map<String, Long> byStatus;
}