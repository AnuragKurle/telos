
(async () => {
    try {
        console.log('Testing dynamic import of dodopayments...');
        const dodoModule = await import('dodopayments');
        console.log('Import successful.');
        console.log('Keys:', Object.keys(dodoModule));
        console.log('Default export:', dodoModule.default);
        console.log('Is constructor?', typeof dodoModule.default === 'function');
    } catch (error) {
        console.error('Import failed:', error);
    }
})();
