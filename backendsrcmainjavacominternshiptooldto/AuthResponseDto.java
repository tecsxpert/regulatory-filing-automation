package com.internship.tool.dto;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class AuthResponseDto {
    private String token;
    private String username;
    private String role;
    private long expiresIn;
}