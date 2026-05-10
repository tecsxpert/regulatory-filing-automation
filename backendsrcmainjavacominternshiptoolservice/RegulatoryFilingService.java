// Add this method to RegulatoryFilingService.java
public void exportCsv(PrintWriter writer) {
    writer.println("ID,Title,Status,Category,Filing Date,Deadline,Submitted By,Created At");

    List<RegulatoryFiling> all = filingRepository.findAllByIsDeletedFalse(Pageable.unpaged()).getContent();
    all.forEach(f -> writer.printf("%d,\"%s\",%s,%s,%s,%s,%s,%s%n",
            f.getId(),
            f.getTitle(),
            f.getStatus(),
            f.getCategory() != null ? f.getCategory() : "",
            f.getFilingDate() != null ? f.getFilingDate() : "",
            f.getDeadlineDate() != null ? f.getDeadlineDate() : "",
            f.getSubmittedBy() != null ? f.getSubmittedBy() : "",
            f.getCreatedAt()
    ));
    writer.flush();
}