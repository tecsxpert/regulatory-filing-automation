package com.internship.tool.scheduler;

import com.internship.tool.entity.RegulatoryFiling;
import com.internship.tool.repository.RegulatoryFilingRepository;
import com.internship.tool.service.EmailService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import java.time.LocalDate;
import java.util.List;

@Component
@RequiredArgsConstructor
@Slf4j
public class FilingReminderScheduler {

    private final RegulatoryFilingRepository filingRepository;
    private final EmailService emailService;

    // Runs every day at 8:00 AM
    @Scheduled(cron = "0 0 8 * * *")
    public void sendOverdueReminders() {
        List<RegulatoryFiling> overdue = filingRepository.findOverdueFilings(LocalDate.now());
        log.info("Found {} overdue filings", overdue.size());
        
        overdue.forEach(filing -> {
            try {
                emailService.sendOverdueAlert(filing);
            } catch (Exception e) {
                log.error("Failed to send overdue alert for filing {}", filing.getId(), e);
            }
        });
    }

    // 7-day advance deadline alert — runs every day at 9:00 AM
    @Scheduled(cron = "0 0 9 * * *")
    public void sendUpcomingDeadlineAlerts() {
        LocalDate today = LocalDate.now();
        LocalDate sevenDaysLater = today.plusDays(7);
        
        List<RegulatoryFiling> upcoming = filingRepository.findUpcomingDeadlines(today, sevenDaysLater);
        log.info("Found {} filings with deadlines in 7 days", upcoming.size());
        
        upcoming.forEach(filing -> {
            try {
                emailService.sendDeadlineAlert(filing);
            } catch (Exception e) {
                log.error("Failed to send deadline alert for filing {}", filing.getId(), e);
            }
        });
    }

    // Weekly summary every Monday at 7:00 AM
    @Scheduled(cron = "0 0 7 * * MON")
    public void sendWeeklySummary() {
        long total = filingRepository.count();
        List<RegulatoryFiling> overdue = filingRepository.findOverdueFilings(LocalDate.now());
        
        log.info("Weekly summary — total: {}, overdue: {}", total, overdue.size());
        
        try {
            emailService.sendWeeklySummary(total, overdue.size());
        } catch (Exception e) {
            log.error("Failed to send weekly summary", e);
        }
    }
}