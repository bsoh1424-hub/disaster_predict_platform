package com.disaster.stormsurge.dto;

import java.time.LocalDateTime;

public class AuthDto {

    public record LoginRequest(String username, String password) {}

    public record RegisterRequest(String username, String password, String name, String department) {}

    public record AuthResponse(String token, String username, String name, String role, String department) {}

    public record UserInfoResponse(Long id, String username, String name, String role, String department, LocalDateTime createdAt) {}
}
