package com.internship.tool.controller;

import com.internship.tool.dto.FilingRequestDto;
import com.internship.tool.dto.FilingResponseDto;
import com.internship.tool.dto.StatsDto;
import com.internship.tool.service.RegulatoryFilingService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/filings")
@RequiredArgsConstructor
@Tag(name = "Regulatory Filing", description = "Regulatory filing management APIs")
public class RegulatoryFilingController {

    private final RegulatoryFilingService filingService;

    @Operation(summary = "Update a filing")
    @ApiResponse(responseCode = "200", description = "Updated successfully")
    @ApiResponse(responseCode = "404", description = "Filing not found")
    @PutMapping("/{id}")
    @PreAuthorize("hasAnyRole('ADMIN', 'MANAGER')")
    public ResponseEntity<FilingResponseDto> update(
            @PathVariable Long id,
            @Valid @RequestBody FilingRequestDto request) {
        return ResponseEntity.ok(filingService.update(id, request));
    }

    @Operation(summary = "Soft delete a filing")
    @ApiResponse(responseCode = "204", description = "Deleted successfully")
    @DeleteMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        filingService.softDelete(id);
        return ResponseEntity.noContent().build();
    }

    @Operation(summary = "Search filings by keyword")
    @GetMapping("/search")
    public ResponseEntity<Page<FilingResponseDto>> search(
            @RequestParam String q,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(defaultValue = "createdAt") String sortBy,
            @RequestParam(defaultValue = "desc") String sortDir) {

        Sort sort = sortDir.equalsIgnoreCase("asc")
                ? Sort.by(sortBy).ascending()
                : Sort.by(sortBy).descending();
        Pageable pageable = PageRequest.of(page, size, sort);
        return ResponseEntity.ok(filingService.search(q, pageable));
    }

    @Operation(summary = "Get dashboard statistics")
    @GetMapping("/stats")
    public ResponseEntity<StatsDto> getStats() {
        return ResponseEntity.ok(filingService.getStats());
    }
}