package com.example.service.impl;

import com.example.service.UserService;
import com.example.model.User;
import com.example.util.LoggerUtil;
import java.util.HashMap;
import java.util.Map;

/**
 * Implementation of UserService interface.
 * Provides in-memory user management with validation.
 */
public class UserServiceImpl implements UserService {
    private final Map<Integer, User> userDatabase = new HashMap<>();
    
    @Override
    public boolean validateUser(User user) {
        if (user == null) {
            LoggerUtil.log("Validation failed: User is null");
            return false;
        }
        
        if (user.getName() == null || user.getName().trim().isEmpty()) {
            LoggerUtil.log("Validation failed: Name is empty");
            return false;
        }
        
        if (user.getEmail() == null || !user.getEmail().contains("@")) {
            LoggerUtil.log("Validation failed: Invalid email");
            return false;
        }
        
        LoggerUtil.log("User validation passed: " + user.getName());
        return true;
    }
    
    @Override
    public boolean saveUser(User user) {
        if (!validateUser(user)) {
            return false;
        }
        
        userDatabase.put(user.getId(), user);
        LoggerUtil.log("User saved to database: ID=" + user.getId());
        return true;
    }
    
    @Override
    public User getUserById(int id) {
        User user = userDatabase.get(id);
        if (user == null) {
            LoggerUtil.log("User not found: ID=" + id);
        }
        return user;
    }
    
    @Override
    public boolean deleteUser(int id) {
        if (userDatabase.containsKey(id)) {
            userDatabase.remove(id);
            LoggerUtil.log("User deleted: ID=" + id);
            return true;
        }
        LoggerUtil.log("Delete failed: User not found ID=" + id);
        return false;
    }
}
