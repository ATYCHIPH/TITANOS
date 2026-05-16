/**
 * TITANOS Auth Service Abstraction
 * Currently uses local storage for mock implementation.
 * Can be replaced with Supabase/Auth.js/etc.
 */

const STORAGE_KEY = 'titanos_session';

class AuthService {
  constructor() {
    this.user = JSON.parse(localStorage.getItem(STORAGE_KEY)) || null;
  }

  async login(email, password) {
    // Mock login logic
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        if (email && password) {
          const user = {
            id: 'u1',
            email,
            name: email.split('@')[0],
            onboarded: localStorage.getItem('titanos_onboarded') === 'true',
          };
          this.user = user;
          localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
          resolve(user);
        } else {
          reject(new Error('Invalid email or password'));
        }
      }, 800);
    });
  }

  async signup(name, email, password) {
    return new Promise((resolve) => {
      setTimeout(() => {
        const user = { id: 'u1', name, email, onboarded: false };
        this.user = user;
        localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
        resolve(user);
      }, 800);
    });
  }

  async logout() {
    this.user = null;
    localStorage.removeItem(STORAGE_KEY);
    return Promise.resolve();
  }

  async forgotPassword(email) {
    console.log('Forgot password for:', email);
    return new Promise(resolve => setTimeout(resolve, 800));
  }

  async resetPassword(token, newPassword) {
    console.log('Reset password with token:', token);
    return new Promise(resolve => setTimeout(resolve, 800));
  }

  isAuthenticated() {
    return !!this.user;
  }

  isOnboarded() {
    return this.user?.onboarded || false;
  }

  completeOnboarding() {
    if (this.user) {
      this.user.onboarded = true;
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.user));
      localStorage.setItem('titanos_onboarded', 'true');
    }
  }

  getCurrentUser() {
    return this.user;
  }
}

export const authService = new AuthService();
