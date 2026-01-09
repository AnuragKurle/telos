// Test sending to verified Gmail address first
import sgMail from '@sendgrid/mail';
import dotenv from 'dotenv';

dotenv.config();

const apiKey = process.env.SENDGRID_API_KEY;
if (!apiKey) {
    console.error('❌ Error: SENDGRID_API_KEY not found in environment variables.');
    process.exit(1);
}
sgMail.setApiKey(apiKey);

const msg = {
    to: 'anuragkurle@gmail.com',  // Test to your Gmail first
    from: {
        email: 'anuragkurle@gmail.com',
        name: 'Telos Screen Tracker'
    },
    subject: 'SendGrid Verification Test',
    text: 'If you receive this, your sender is verified!',
    html: '<h2>✅ Success!</h2><p>Your SendGrid sender email is verified and working.</p><p>Next test will be sent to anurag@userology.co</p>',
};

console.log('Testing sender verification with Gmail first...');

sgMail
    .send(msg)
    .then(() => {
        console.log('✅ Email sent to Gmail successfully!');
        console.log('📧 Sender is verified! Now testing with userology.co...\n');

        // Now send to userology
        const msg2 = {
            to: 'anurag@userology.co',
            from: {
                email: 'anuragkurle@gmail.com',
                name: 'Telos Screen Tracker'
            },
            subject: 'Test Email - Daily Activity Report',
            text: 'This is a test email from your Telos backend!',
            html: '<strong>This is a test email from your Telos backend!</strong><p>If you can read this, SendGrid is working correctly! 🎉</p>',
        };

        return sgMail.send(msg2);
    })
    .then(() => {
        console.log('✅ Email sent to userology.co successfully!');
        console.log('📧 Check inbox at anurag@userology.co');
    })
    .catch((error) => {
        console.error('❌ Error:', error.message);
        if (error.response) {
            console.error('Details:', error.response.body.errors);
        }
    });
