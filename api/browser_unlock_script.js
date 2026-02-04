// ReconX Frontend Lockout Clearer - Run this in browser console
// Copy and paste this entire script into your browser's developer console

console.log("🔓 ReconX Login Lockout Clearer");
console.log("=" * 40);

try {
    // Check current status
    const fails = Number(localStorage.getItem('loginFails') || '0');
    const lastFail = Number(localStorage.getItem('loginLastFail') || '0');
    const lastFailDate = lastFail ? new Date(lastFail).toLocaleString() : 'Never';
    
    console.log(`📊 Current Status:`);
    console.log(`   Failed Attempts: ${fails}`);
    console.log(`   Last Failed: ${lastFailDate}`);
    
    // Check if locked
    let isLocked = false;
    if (fails >= 5) {
        const elapsed = Date.now() - lastFail;
        isLocked = elapsed < 5 * 60 * 1000; // 5 minutes
    }
    
    console.log(`   Currently Locked: ${isLocked ? '🔒 YES' : '🔓 NO'}`);
    
    if (isLocked) {
        console.log("🔧 Clearing lockout...");
        
        // Clear the lockout data
        localStorage.removeItem('loginFails');
        localStorage.removeItem('loginLastFail');
        
        console.log("✅ Lockout cleared successfully!");
        console.log("✅ You can now try logging in again.");
        
        // Show success message on page if possible
        const errorEl = document.getElementById('formError');
        if (errorEl) {
            errorEl.textContent = 'Lockout cleared! You can now try logging in.';
            errorEl.className = 'text-green-600';
            errorEl.classList.remove('hidden');
        }
        
    } else {
        console.log("ℹ️  Account is not locked. You can try logging in.");
    }
    
    console.log("\n🎯 Next Steps:");
    console.log("1. Refresh the login page (Ctrl+F5)");
    console.log("2. Try logging in with:");
    console.log("   Username: admin");
    console.log("   Password: admin123");
    
} catch (error) {
    console.error("❌ Error:", error);
    console.log("💡 Try manually clearing localStorage:");
    console.log("   localStorage.removeItem('loginFails')");
    console.log("   localStorage.removeItem('loginLastFail')");
}

console.log("=" * 40);
