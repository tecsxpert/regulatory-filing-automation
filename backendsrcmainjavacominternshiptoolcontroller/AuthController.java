package com.internship.tool.controller;

import com.internship.tool.dto.AuthRequestDto;
import com.internship.tool.dto.AuthResponseDto;
import com.internship.tool.dto.RegisterRequestDto;
import com.internship.tool.service.AuthService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @PostMapping("/login")
    public ResponseEntity<AuthResponseDto> login(@Valid @RequestBody AuthRequestDto request) {
        return ResponseEntity.ok(authService.login(request));
    }

    @PostMapping("/register")
    public ResponseEntity<AuthResponseDto> register(@Valid @RequestBody RegisterRequestDto request) {
        return ResponseEntity.status(201).body(authService.register(request));
    }

    @PostMapping("/refresh")
    public ResponseEntity<AuthResponseDto> refresh(@RequestHeader("Authorization") String bearerToken) {
        String token = bearerToken.replace("Bearer ", "");
        return ResponseEntity.ok(authService.refresh(token));
    }
}