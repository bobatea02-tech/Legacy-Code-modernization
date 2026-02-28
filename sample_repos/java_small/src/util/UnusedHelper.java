package com.example.util;

/**
 * Unused helper class for validation testing.
 * This class is intentionally not referenced anywhere.
 */
public class UnusedHelper {
    /**
     * Unused method that formats strings.
     * @param input Input string
     * @return Formatted string
     */
    public static String formatString(String input) {
        if (input == null) {
            return "";
        }
        return input.trim().toUpperCase();
    }
    
    /**
     * Unused method that validates numbers.
     * @param value Number to validate
     * @return true if positive
     */
    public static boolean isPositive(int value) {
        return value > 0;
    }
}
