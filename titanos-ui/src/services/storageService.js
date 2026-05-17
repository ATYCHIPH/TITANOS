/**
 * TITANOS Secure Storage Service
 * Isolated adapter for managing sensitive data like API keys.
 * Uses local storage with masking for mock implementation.
 * [MOCK ONLY] - TEMPORARY/MOCK: Do not store raw API keys in plain localStorage in production. Use backend secure storage.
 */

const KEYS_STORAGE_KEY = 'titanos_provider_keys';

class StorageService {
  constructor() {
    this.keys = JSON.parse(localStorage.getItem(KEYS_STORAGE_KEY)) || [];
  }

  async saveKey(providerId, keyData) {
    // In a real app, this would send to a secure backend or encrypt locally
    const existingIndex = this.keys.findIndex(k => k.providerId === providerId);
    
    const newKeyEntry = {
      providerId,
      ...keyData,
      id: Math.random().toString(36).substr(2, 9),
      createdAt: new Date().toISOString(),
      // Store a masked version for display
      maskedKey: this._maskKey(keyData.apiKey)
    };

    if (existingIndex > -1) {
      this.keys[existingIndex] = newKeyEntry;
    } else {
      this.keys.push(newKeyEntry);
    }

    this._persist();
    return Promise.resolve(newKeyEntry);
  }

  async deleteKey(providerId) {
    this.keys = this.keys.filter(k => k.providerId !== providerId);
    this._persist();
    return Promise.resolve();
  }

  getKeys() {
    // Never return the actual raw API keys in this list, only metadata and masked version
    return this.keys.map(({ providerId, id, createdAt, maskedKey }) => ({
      providerId,
      id,
      createdAt,
      maskedKey,
    }));
  }

  async getRawKey(providerId) {
    // In a real app, this would involve decryption or a secure fetch
    const entry = this.keys.find(k => k.providerId === providerId);
    return entry ? entry.apiKey : null;
  }

  _maskKey(key) {
    if (!key) return '';
    if (key.length <= 8) return '********';
    return `${key.substring(0, 4)}...${key.substring(key.length - 4)}`;
  }

  _persist() {
    localStorage.setItem(KEYS_STORAGE_KEY, JSON.stringify(this.keys));
  }
}

export const storageService = new StorageService();
