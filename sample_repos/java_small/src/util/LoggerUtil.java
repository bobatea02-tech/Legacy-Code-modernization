package com.example.util;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * Simple logging utility.
 * Provides timestamp-based logging functionality.
 */
public class LoggerUtil {
    private static final DateTimeFormatter formatter = 
        DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    
    /**
     * Logs a message with timestamp.
     * @param message Message to log
     */
    public static void log(String message) {
        String timestamp = LocalDateTime.now().format(formatter);
        System.out.println("[" + timestamp + "] " + message);
    }
    
    /**
     * Logs an error message with timestamp.
     * @param message Error message
     * @param throwable Exception details
     */
    public static void logError(String message, Throwable throwable) {
        String timestamp = LocalDateTime.now().format(formatter);
        System.err.println("[" + timestamp + "] ERROR: " + message);
        if (throwable != null) {
            throwable.printStackTrace();
        }
    }
}
