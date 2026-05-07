package com.internship.tool;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;

@SpringBootApplication
@EnableAsync
public class ToolApplication {
    public static void main(String[] args) {
        SpringApplication.run(ToolApplication.class, args);
    }
}