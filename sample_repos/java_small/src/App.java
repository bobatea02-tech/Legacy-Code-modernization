package com.example.app;

import com.example.service.UserService;
import com.example.service.impl.UserServiceImpl;
import com.example.model.User;
import com.example.util.LoggerUtil;

/**
 * Main application entry point.
 * Demonstrates cross-file dependencies and service usage.
 */
public class App {
    private static final UserService userService = new UserServiceImpl();
    
    public static void main(String[] args) {
        LoggerUtil.log("Application starting...");
        
        // Create and process users
        User user1 = new User(1, "Alice", "alice@example.com");
        User user2 = new User(2, "Bob", "bob@example.com");
        
        // Validate and save users
        if (userService.validateUser(user1)) {
            userService.saveUser(user1);
            LoggerUtil.log("User saved: " + user1.getName());
        }
        
        if (userService.validateUser(user2)) {
            userService.saveUser(user2);
            LoggerUtil.log("User saved: " + user2.getName());
        }
        
        // Retrieve and display user
        User retrieved = userService.getUserById(1);
        if (retrieved != null) {
            LoggerUtil.log("Retrieved user: " + retrieved.toString());
        }
        
        LoggerUtil.log("Application completed successfully.");
    }
}
