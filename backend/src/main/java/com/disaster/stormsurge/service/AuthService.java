package com.disaster.stormsurge.service;

import com.disaster.stormsurge.dto.AuthDto.*;
import com.disaster.stormsurge.entity.User;
import com.disaster.stormsurge.repository.UserRepository;
import com.disaster.stormsurge.security.JwtTokenProvider;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider tokenProvider;

    public AuthService(UserRepository userRepository, PasswordEncoder passwordEncoder, JwtTokenProvider tokenProvider) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.tokenProvider = tokenProvider;
    }

    @Transactional
    public AuthResponse register(RegisterRequest req) {
        if (userRepository.existsByUsername(req.username())) {
            throw new IllegalArgumentException("이미 존재하는 아이디입니다: " + req.username());
        }

        User user = new User(
                req.username(),
                passwordEncoder.encode(req.password()),
                req.name(),
                req.department(),
                "ROLE_USER"
        );
        userRepository.save(user);

        String token = tokenProvider.generateToken(user.getUsername(), user.getRole(), user.getName());
        return new AuthResponse(token, user.getUsername(), user.getName(), user.getRole(), user.getDepartment());
    }

    public AuthResponse login(LoginRequest req) {
        User user = userRepository.findByUsername(req.username())
                .orElseThrow(() -> new BadCredentialsException("아이디 또는 비밀번호가 일치하지 않습니다."));

        if (!passwordEncoder.matches(req.password(), user.getPassword())) {
            throw new BadCredentialsException("아이디 또는 비밀번호가 일치하지 않습니다.");
        }

        String token = tokenProvider.generateToken(user.getUsername(), user.getRole(), user.getName());
        return new AuthResponse(token, user.getUsername(), user.getName(), user.getRole(), user.getDepartment());
    }

    @Transactional
    public UserInfoResponse updateProfile(String username, UpdateProfileRequest req) {
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new IllegalArgumentException("사용자를 찾을 수 없습니다: " + username));
        if (req.name() != null && !req.name().isBlank()) {
            user.setName(req.name().trim());
        }
        if (req.department() != null) {
            user.setDepartment(req.department().trim());
        }
        userRepository.save(user);
        return new UserInfoResponse(user.getId(), user.getUsername(), user.getName(), user.getRole(), user.getDepartment(), user.getCreatedAt());
    }

    @Transactional
    public void changePassword(String username, ChangePasswordRequest req) {
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new IllegalArgumentException("사용자를 찾을 수 없습니다: " + username));
        if (!passwordEncoder.matches(req.currentPassword(), user.getPassword())) {
            throw new BadCredentialsException("현재 비밀번호가 일치하지 않습니다.");
        }
        if (req.newPassword() == null || req.newPassword().length() < 4) {
            throw new IllegalArgumentException("새 비밀번호는 4자 이상이어야 합니다.");
        }
        user.setPassword(passwordEncoder.encode(req.newPassword()));
        userRepository.save(user);
    }

    @Transactional
    public void deleteAccount(String username) {
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new IllegalArgumentException("사용자를 찾을 수 없습니다: " + username));
        userRepository.delete(user);
    }

    public UserInfoResponse getUserInfo(String username) {
        User user = userRepository.findByUsername(username)
                .orElseThrow(() -> new IllegalArgumentException("사용자를 찾을 수 없습니다: " + username));
        return new UserInfoResponse(user.getId(), user.getUsername(), user.getName(), user.getRole(), user.getDepartment(), user.getCreatedAt());
    }
}
