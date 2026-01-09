// Send demo email with improved report
import sgMail from '@sendgrid/mail';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const apiKey = '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';
sgMail.setApiKey(apiKey);

// Read the improved report HTML
const reportPath = join(__dirname, '../client/reports/templates/test_improved_report.html');
const htmlContent = readFileSync(reportPath, 'utf-8');

const msg = {
    to: 'anurag@userology.co',
    from: {
        email: 'anuragkurle27@gmail.com',
        name: 'Telos Daily Report'
    },
    subject: '✨ Telos Daily Report — January 09, 2026',
    text: 'Your daily activity report is ready! Please view this email in an HTML-enabled client for the best experience.',
    html: htmlContent,
};

console.log('📧 Sending improved daily report to anurag@userology.co...');

sgMail
    .send(msg)
    .then(() => {
        console.log('✅ Email sent successfully!');
        console.log('📬 Check your inbox at anurag@userology.co');
    })
    .catch((error) => {
        console.error('❌ Error:', error.message);
        if (error.response) {
            console.error('Details:', error.response.body.errors);
        }
    });
