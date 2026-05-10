package com.internship.tool.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.internship.tool.entity.AuditLog;
import com.internship.tool.repository.AuditLogRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

@Aspect
@Component
@RequiredArgsConstructor
@Slf4j
public class AuditAspect {

    private final AuditLogRepository auditLogRepository;
    private final ObjectMapper objectMapper;

    @Around("execution(* com.internship.tool.service.RegulatoryFilingService.create(..)) || " +
            "execution(* com.internship.tool.service.RegulatoryFilingService.update(..)) || " +
            "execution(* com.internship.tool.service.RegulatoryFilingService.softDelete(..))")
    public Object logAudit(ProceedingJoinPoint joinPoint) throws Throwable {
        String methodName = joinPoint.getSignature().getName();
        Object[] args = joinPoint.getArgs();

        String action = switch (methodName) {
            case "create" -> "CREATE";
            case "update" -> "UPDATE";
            case "softDelete" -> "DELETE";
            default -> methodName.toUpperCase();
        };

        String performer = getCurrentUser();
        String newValue = null;
        Long entityId = null;

        try {
            if (args.length > 0) {
                newValue = objectMapper.writeValueAsString(args[args.length - 1]);
            }
            if (args.length > 1 && args[0] instanceof Long) {
                entityId = (Long) args[0];
            }
        } catch (Exception e) {
            log.warn("Could not serialize audit args", e);
        }

        Object result = joinPoint.proceed();

        try {
            if (result != null && !"DELETE".equals(action)) {
                newValue = objectMapper.writeValueAsString(result);
                if (entityId == null) {
                    var idField = result.getClass().getDeclaredField("id");
                    idField.setAccessible(true);
                    entityId = (Long) idField.get(result);
                }
            }
        } catch (Exception e) {
            log.warn("Could not serialize audit result", e);
        }

        AuditLog auditLog = AuditLog.builder()
                .entityType("RegulatoryFiling")
                .entityId(entityId)
                .action(action)
                .performedBy(performer)
                .newValue(newValue)
                .createdAt(LocalDateTime.now())
                .build();

        auditLogRepository.save(auditLog);
        return result;
    }

    private String getCurrentUser() {
        try {
            return SecurityContextHolder.getContext()
                    .getAuthentication()
                    .getName();
        } catch (Exception e) {
            return "system";
        }
    }
}