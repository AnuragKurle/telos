/**
 * Setup Script - Initialize Firestore with Prompts from Local Files
 * 
 * Run this script to sync local prompts (from ../client/prompts/) to Firestore.
 * This uses the local prompt files as the source of truth.
 * 
 * Usage:
 *   node setup-firestore-prompts.js
 */

import admin from 'firebase-admin';
import dotenv from 'dotenv';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Load environment variables
dotenv.config();

// Get directory path (for ES modules)
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Initialize Firebase Admin
const projectId = process.env.FIREBASE_PROJECT_ID;

if (!projectId) {
  console.error('❌ FIREBASE_PROJECT_ID not set in .env file');
  process.exit(1);
}

admin.initializeApp({
  projectId: projectId,
});

const db = admin.firestore();

// Define prompt mappings (Firestore ID -> local file)
const PROMPT_FILES = {
  'screenshot-analysis': {
    file: '../client/prompts/screenshot_analysis.txt',
    description: 'Screenshot analysis prompt for categorizing user activity',
  },
  'session-enrichment': {
    file: '../client/prompts/session_enrichment.txt',
    description: 'Session analysis prompt for generating session summaries',
  },
  'daily-summary': {
    file: '../client/prompts/daily_summary.txt',
    description: 'Daily summary prompt for end-of-day insights',
  },
  'ai-chat-system': {
    file: '../client/prompts/ai_chat_system.txt',
    description: 'AI chat system prompt for interactive queries',
  },
};

/**
 * Read prompt content from local file
 */
function readPromptFile(filePath) {
  const fullPath = path.resolve(__dirname, filePath);
  if (!fs.existsSync(fullPath)) {
    throw new Error(`Prompt file not found: ${fullPath}`);
  }
  return fs.readFileSync(fullPath, 'utf-8').trim();
}

/**
 * Upload a single prompt to Firestore
 */
async function uploadPrompt(promptId, config) {
  try {
    console.log(`📝 Uploading: ${promptId}...`);

    // Read content from local file
    const content = readPromptFile(config.file);

    // Create/update the main prompt document
    const promptRef = db.collection('prompts').doc(promptId);
    await promptRef.set({
      activeVersion: 'v1',
      updatedAt: admin.firestore.FieldValue.serverTimestamp(),
      description: config.description,
    });

    // Create/update version v1
    const versionRef = promptRef.collection('versions').doc('v1');
    await versionRef.set({
      content: content,
      createdAt: admin.firestore.FieldValue.serverTimestamp(),
      metadata: {
        author: 'system',
        note: 'Synced from local prompts folder',
        source: config.file,
      },
    });

    console.log(`✅ Uploaded: ${promptId} (${content.length} chars)`);
  } catch (error) {
    console.error(`❌ Failed to upload ${promptId}:`, error.message);
    throw error;
  }
}

async function setupPrompts() {
  try {
    console.log('🔄 Syncing local prompts to Firestore...\n');
    console.log('Source: ../client/prompts/\n');

    // Upload all prompts
    for (const [promptId, config] of Object.entries(PROMPT_FILES)) {
      await uploadPrompt(promptId, config);
    }

    console.log('\n🎉 All prompts synced successfully!\n');
    console.log('Uploaded prompts:');
    Object.keys(PROMPT_FILES).forEach(id => console.log(`  - ${id}`));
    console.log('\nYou can now:');
    console.log('1. Start the backend with: npm run dev');
    console.log('2. View prompts in Firebase Console (under prompts collection)');
    console.log('3. Re-run this script anytime to sync updates from local files\n');

    process.exit(0);
  } catch (error) {
    console.error('\n❌ Setup failed:', error.message);
    console.error('\nMake sure:');
    console.error('1. You have Firestore enabled in Firebase Console');
    console.error('2. Your .env file has correct FIREBASE_PROJECT_ID');
    console.error('3. You are authenticated with: gcloud auth application-default login');
    console.error('4. Local prompt files exist in ../client/prompts/\n');
    process.exit(1);
  }
}

// Run setup
setupPrompts();

