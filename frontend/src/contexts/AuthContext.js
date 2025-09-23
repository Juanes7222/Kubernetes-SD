import React, { createContext, useContext, useEffect, useState } from 'react';
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signInWithPopup,
  signOut,
  onAuthStateChanged,
  updateProfile
} from 'firebase/auth';
import { auth, googleProvider } from '../lib/firebase';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [idToken, setIdToken] = useState(null);

  // Sign up function
  const signup = async (email, password, displayName) => {
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    
    // Update display name
    if (displayName) {
      await updateProfile(userCredential.user, {
        displayName: displayName
      });
    }
    
    return userCredential;
  };

  // Sign in function
  const login = (email, password) => {
    return signInWithEmailAndPassword(auth, email, password);
  };

  // Google sign in function
  const loginWithGoogle = () => {
    return signInWithPopup(auth, googleProvider);
  };

  // Sign out function
  const logout = () => {
    return signOut(auth);
  };

  // Get current ID token and verify with our backend
  const getIdToken = async () => {
    if (user) {
      try {
        // Get Firebase token
        const firebaseToken = await user.getIdToken();
        
        // Verify token with our backend
        const response = await fetch(`${process.env.REACT_APP_AUTH_SERVICE_URL}/api/auth/verify`, {
          headers: {
            'Authorization': `Bearer ${firebaseToken}`
          }
        });
        
        if (!response.ok) {
          console.error('Token verification failed');
          return null;
        }
        
        return firebaseToken;
      } catch (error) {
        console.error('Error verifying token:', error);
        return null;
      }
    }
    return null;
  };

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      setUser(user);
      
      if (user) {
        try {
          // Get Firebase token
          const firebaseToken = await user.getIdToken();
          
          // Verify token with our backend
          const response = await fetch(`${process.env.REACT_APP_AUTH_SERVICE_URL}/api/auth/verify`, {
            headers: {
              'Authorization': `Bearer ${firebaseToken}`
            }
          });
          
          if (response.ok) {
            setIdToken(firebaseToken);
          } else {
            console.error('Token verification failed');
            setIdToken(null);
          }
        } catch (error) {
          console.error('Error verifying token:', error);
          setIdToken(null);
        }
      } else {
        setIdToken(null);
      }
      
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  const value = {
    user,
    idToken,
    signup,
    login,
    loginWithGoogle,
    logout,
    getIdToken
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};