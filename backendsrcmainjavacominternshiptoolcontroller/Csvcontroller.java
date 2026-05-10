// Add this import
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;

// Add this method to RegulatoryFilingController.java
@Operation(summary = "Export all filings as CSV")
@GetMapping("/export")
@PreAuthorize("hasAnyRole('ADMIN', 'MANAGER')")
public void exportCsv(HttpServletResponse response) throws IOException {
    response.setContentType("text/csv");
    response.setHeader("Content-Disposition", "attachment; filename=filings.csv");
    filingService.exportCsv(response.getWriter());
}