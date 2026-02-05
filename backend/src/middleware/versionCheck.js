/**
 * Client Version Check Middleware
 * 
 * Validates X-Client-Version header and enforces minimum version requirement.
 * Returns 426 Upgrade Required if client is too old.
 */

/**
 * Parse semantic version string (e.g., "0.1.0") to comparable number
 * 
 * @param {string} version - Version string in format "major.minor.patch"
 * @returns {number} Numeric representation for comparison
 */
function parseVersion(version) {
  if (!version || typeof version !== 'string') {
    return 0;
  }

  const parts = version.split('.').map(Number);
  
  // Handle invalid version format
  if (parts.length !== 3 || parts.some(isNaN)) {
    return 0;
  }

  const [major, minor, patch] = parts;
  
  // Create comparable number: major * 1000000 + minor * 1000 + patch
  // Examples: 0.1.0 -> 1000, 1.0.0 -> 1000000, 0.2.5 -> 2005
  return major * 1000000 + minor * 1000 + patch;
}

/**
 * Middleware to check client version against minimum required version
 * 
 * Expects: X-Client-Version header (e.g., "0.1.0")
 * 
 * On success: Continues to next middleware
 * On failure: Returns 426 Upgrade Required
 */
export function checkClientVersion(req, res, next) {
  const clientVersion = req.headers['x-client-version'];
  const minVersion = process.env.MIN_CLIENT_VERSION || '0.1.0';

  // If no version header provided, reject
  if (!clientVersion) {
    return res.status(426).json({
      error: 'ClientVersionError',
      message: 'X-Client-Version header is required',
      minimum_version: minVersion,
      download_url: 'https://github.com/yourrepo/telos/releases',
      code: 'MISSING_VERSION_HEADER',
    });
  }

  // Parse versions for comparison
  const clientVersionNum = parseVersion(clientVersion);
  const minVersionNum = parseVersion(minVersion);

  // Check if client version is too old
  if (clientVersionNum < minVersionNum) {
    return res.status(426).json({
      error: 'ClientVersionError',
      message: `Client version ${clientVersion} is too old. Minimum required: ${minVersion}`,
      minimum_version: minVersion,
      download_url: 'https://github.com/yourrepo/telos/releases',
      code: 'CLIENT_TOO_OLD',
    });
  }

  // Version is acceptable, continue
  next();
}

/**
 * Optional: Middleware that only logs version but doesn't block
 * Useful for monitoring version adoption
 */
export function logClientVersion(req, res, next) {
  const clientVersion = req.headers['x-client-version'];
  if (clientVersion) {
    console.log(`[Version] Client version: ${clientVersion}, User: ${req.user?.uid || 'unknown'}`);
  }
  next();
}

export default checkClientVersion;


