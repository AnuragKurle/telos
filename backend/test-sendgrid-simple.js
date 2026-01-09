// Test with CORRECT verified sender email
import sgMail from '@sendgrid/mail';

const apiKey = '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';
sgMail.setApiKey(apiKey);

const msg = {
    to: 'anurag@userology.co',
    from: {
        email: 'anuragkurle27@gmail.com',  // FIXED: using verified sender
        name: 'Telos Tracker'
    },
    subject: '📊 Test Email - Daily Activity Report',
    text: 'This is a test email from your Telos backend!',
    html: '<strong>This is a test email from your Telos backend!</strong><p>If you can read this, SendGrid is working correctly! 🎉</p>',
};

console.log('Sending test email to anurag@userology.co (from verified sender anuragkurle27@gmail.com)...');

sgMail
    .send(msg)
    .then(() => {
        console.log('✅ Email sent successfully!');
        console.log('📧 Check your inbox at anurag@userology.co');
    })
    .catch((error) => {
        console.error('❌ Error:', error.message);
        if (error.response) {
            console.error('Details:', error.response.body.errors);
        }
    });
