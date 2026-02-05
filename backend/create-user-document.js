/**
 * Create user document in Firestore
 * This script initializes Firebase and creates the user document directly
 */

import { initializeFirebase, getFirestore } from './src/config/firebase.js';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

// Initialize Firebase
initializeFirebase();

const db = getFirestore();

async function createUserDocument() {
    const email = process.argv[2] || 'anurag@userology.co';
    const uid = process.argv[3] || 'UQgcLrVEb5bQl7d1aBhSSGzXNCD2';  // Default or from args

    console.log(`\n📧 Creating user document for: ${email}`);

    const userRef = db.collection('users').doc(email);

    // Check if already exists
    const existing = await userRef.get();
    if (existing.exists) {
        console.log('⚠️  User document already exists!');
        console.log('📄 Current data:', JSON.stringify(existing.data(), null, 2));

        // Update with email reports enabled and fix accessStatus
        await userRef.update({
            'accessStatus': 'pro',  // Critical: this is the field auth.js checks
            'emailReports.enabled': true,
            'emailReports.timezone': 'Asia/Kolkata',
            'emailReports.preferredHour': 21,
            'emailReports.frequency': 'daily',
            'status': 'active',
            'plan': 'pro'
        });
        console.log('✅ Updated existing document with email reports enabled');
        process.exit(0);
    }

    // Create new user document
    const now = new Date();
    const userData = {
        // Identity
        email: email,
        uid: uid,

        // Access Status (critical: this is what auth.js checks)
        accessStatus: 'pro',

        // Status & Plan
        status: 'active',
        plan: 'pro',

        // Timestamps
        createdAt: now,
        activatedAt: now,
        lastActiveAt: now,

        // Profile
        profile: {
            displayName: 'Anurag',
            timezone: 'Asia/Kolkata',
            source: 'founder'
        },

        // Subscription
        subscription: {
            plan: 'pro',
            billingCycle: null,
            startDate: now,
            endDate: null
        },

        // Trial (not active for pro)
        trial: {
            isActive: false
        },

        // Email Reports
        emailReports: {
            enabled: true,
            timezone: 'Asia/Kolkata',
            preferredHour: 21,  // 9 PM IST
            frequency: 'daily',
            lastSentAt: null,
            unsubscribedAt: null
        },

        // API Usage (will be populated by rate limiter)
        apiUsage: {
            hourBucket: null,
            hourlyCount: 0,
            dayBucket: null,
            dailyCount: 0,
            totalRequests: 0,
            lastRequestAt: null
        },

        // Payment Intent
        paymentIntent: {
            hasRequestedUpgrade: false,
            requestedAt: null,
            requestCount: 0
        },

        // Flags
        flags: {
            isBeta: true,
            isAdmin: true,
            bypassRateLimit: true
        }
    };

    try {
        await userRef.set(userData);
        console.log('✅ User document created successfully!');
        console.log('\n📄 Created with:');
        console.log(`   Email: ${email}`);
        console.log(`   UID: ${uid}`);
        console.log(`   Status: active`);
        console.log(`   Plan: pro`);
        console.log(`   Email Reports: enabled`);
        console.log(`   Report Time: 9 PM IST (21:00)`);
        console.log('\n🎉 Daily reports will now be sent to this email!');
    } catch (error) {
        console.error('❌ Error creating user:', error.message);
        process.exit(1);
    }

    process.exit(0);
}

createUserDocument();
