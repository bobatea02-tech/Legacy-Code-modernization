package com.example.service;

import com.example.model.User;

/**
 * User service interface.
 * Defines contract for user management operations.
 */
public interface UserService {
    /**
     * Validates user data.
     * @param user User to validate
     * @return true if valid, false otherwise
     */
    boolean validateUser(User user);
    
    /**
     * Saves user to storage.
     * @param user User to save
     * @return true if saved successfully
     */
    boolean saveUser(User user);
    
    /**
     * Retrieves user by ID.
     * @param id User ID
     * @return User object or null if not found
     */
    User getUserById(int id);
    
    /**
     * Deletes user by ID.
     * @param id User ID
     * @return true if deleted successfully
     */
    boolean deleteUser(int id);
}
