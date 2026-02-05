/**
 * Encryption Service
 * 
 * Provides AES-256-GCM encryption/decryption for sensitive data
 * stored in Firestore. Uses a key from GCP Secret Manager.
 * 
 * Design:
 *  - encrypt(plaintext) -> base64 string containing IV + authTag + ciphertext
 *  - decrypt(encoded)   -> original plaintext
 *  - encryptFields(obj, fieldNames) -> obj with specified fields encrypted
 *  - decryptFields(obj, fieldNames) -> obj with specified fields decrypted
 */

import crypto from 'crypto';
import { getSecret } from './secrets.js';

const ALGORITHM = 'aes-256-gcm';
const IV_LENGTH = 16;       // 128-bit IV for GCM
const AUTH_TAG_LENGTH = 16;  // 128-bit auth tag
const KEY_LENGTH = 32;       // 256-bit key

let encryptionKey = null;

/**
 * Initialize the encryption key from Secret Manager.
 * Called lazily on first encrypt/decrypt, or eagerly at startup.
 */
export async function initializeEncryption() {
    if (encryptionKey) return;

    try {
        const secretName = process.env.DATA_ENCRYPTION_KEY_SECRET_NAME || 'DATA_ENCRYPTION_KEY';
        const keyHex = await getSecret(secretName);

        // Key should be a 64-char hex string (32 bytes)
        if (!keyHex || keyHex.length < 64) {
            throw new Error('DATA_ENCRYPTION_KEY must be a 64-character hex string (256 bits)');
        }

        encryptionKey = Buffer.from(keyHex.slice(0, 64), 'hex');
        console.log('[ENCRYPTION] Initialized successfully');
    } catch (error) {
        console.error('[ENCRYPTION] Failed to initialize:', error.message);
        console.warn('[ENCRYPTION] Data will be stored unencrypted until key is configured');
    }
}

/**
 * Encrypt a plaintext string.
 * Returns a base64 string: IV (16B) + authTag (16B) + ciphertext
 * 
 * @param {string} plaintext - Text to encrypt
 * @returns {string} Base64-encoded encrypted payload, or original text if encryption unavailable
 */
export function encrypt(plaintext) {
    if (!encryptionKey) {
        // Graceful degradation: return plaintext if key not configured
        return plaintext;
    }

    if (plaintext === null || plaintext === undefined) {
        return plaintext;
    }

    const text = typeof plaintext === 'string' ? plaintext : JSON.stringify(plaintext);

    const iv = crypto.randomBytes(IV_LENGTH);
    const cipher = crypto.createCipheriv(ALGORITHM, encryptionKey, iv, {
        authTagLength: AUTH_TAG_LENGTH
    });

    let encrypted = cipher.update(text, 'utf8');
    encrypted = Buffer.concat([encrypted, cipher.final()]);
    const authTag = cipher.getAuthTag();

    // Pack: IV + authTag + ciphertext
    const packed = Buffer.concat([iv, authTag, encrypted]);
    return 'enc:' + packed.toString('base64');
}

/**
 * Decrypt an encrypted string.
 * Expects base64 string prefixed with "enc:" containing IV + authTag + ciphertext.
 * 
 * @param {string} encoded - Encrypted payload from encrypt()
 * @returns {string} Original plaintext, or the input unchanged if not encrypted
 */
export function decrypt(encoded) {
    if (!encryptionKey) {
        return encoded;
    }

    if (encoded === null || encoded === undefined) {
        return encoded;
    }

    // If not prefixed with "enc:", it's plaintext (backward compatible)
    if (typeof encoded !== 'string' || !encoded.startsWith('enc:')) {
        return encoded;
    }

    const packed = Buffer.from(encoded.slice(4), 'base64');

    if (packed.length < IV_LENGTH + AUTH_TAG_LENGTH + 1) {
        console.warn('[ENCRYPTION] Invalid encrypted payload (too short)');
        return encoded;
    }

    const iv = packed.subarray(0, IV_LENGTH);
    const authTag = packed.subarray(IV_LENGTH, IV_LENGTH + AUTH_TAG_LENGTH);
    const ciphertext = packed.subarray(IV_LENGTH + AUTH_TAG_LENGTH);

    const decipher = crypto.createDecipheriv(ALGORITHM, encryptionKey, iv, {
        authTagLength: AUTH_TAG_LENGTH
    });
    decipher.setAuthTag(authTag);

    let decrypted = decipher.update(ciphertext);
    decrypted = Buffer.concat([decrypted, decipher.final()]);
    return decrypted.toString('utf8');
}

/**
 * Encrypt a JSON-serializable value (object, array, etc.).
 * Serializes to JSON, encrypts, returns base64 string.
 * 
 * @param {*} value - Value to encrypt
 * @returns {string} Encrypted base64 string
 */
export function encryptJSON(value) {
    if (value === null || value === undefined) return value;
    return encrypt(JSON.stringify(value));
}

/**
 * Decrypt back to a parsed JSON value.
 * 
 * @param {string} encoded - Encrypted payload
 * @returns {*} Parsed JSON value
 */
export function decryptJSON(encoded) {
    if (encoded === null || encoded === undefined) return encoded;
    const decrypted = decrypt(encoded);
    try {
        return JSON.parse(decrypted);
    } catch {
        // If it can't be parsed, it was stored as plain text (backward compatible)
        return decrypted;
    }
}

/**
 * Encrypt specified fields of an object (in place).
 * Non-existent fields are skipped.
 * 
 * @param {Object} obj - Object to modify
 * @param {string[]} fields - Field names to encrypt
 * @returns {Object} The same object with fields encrypted
 */
export function encryptFields(obj, fields) {
    if (!obj || !encryptionKey) return obj;

    for (const field of fields) {
        if (obj[field] !== undefined && obj[field] !== null) {
            if (typeof obj[field] === 'object') {
                obj[field] = encryptJSON(obj[field]);
            } else {
                obj[field] = encrypt(String(obj[field]));
            }
        }
    }
    return obj;
}

/**
 * Decrypt specified fields of an object (in place).
 * Non-existent fields are skipped. Handles both encrypted and plaintext gracefully.
 * 
 * @param {Object} obj - Object to modify
 * @param {string[]} fields - Field names to decrypt
 * @param {string[]} [jsonFields=[]] - Subset of fields that should be JSON-parsed after decryption
 * @returns {Object} The same object with fields decrypted
 */
export function decryptFields(obj, fields, jsonFields = []) {
    if (!obj) return obj;

    for (const field of fields) {
        if (obj[field] !== undefined && obj[field] !== null) {
            if (jsonFields.includes(field)) {
                obj[field] = decryptJSON(obj[field]);
            } else {
                obj[field] = decrypt(obj[field]);
            }
        }
    }
    return obj;
}

/**
 * Check if the encryption service is active (key loaded).
 * @returns {boolean}
 */
export function isEncryptionActive() {
    return encryptionKey !== null;
}

export default {
    initializeEncryption,
    encrypt,
    decrypt,
    encryptJSON,
    decryptJSON,
    encryptFields,
    decryptFields,
    isEncryptionActive,
};
