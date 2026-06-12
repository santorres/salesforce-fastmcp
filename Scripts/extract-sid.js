#!/usr/bin/env node

import { execSync } from 'child_process';
import fs from 'fs';
import os from 'os';
import path from 'path';
import crypto from 'crypto';

/**
 * Get Chrome's encryption key from macOS keychain
 */
function getChromeEncryptionKey() {
  try {
    // Try direct security command to get Chrome Safe Storage password
    const password = execSync(
      'security find-generic-password -w -s "Chrome Safe Storage"',
      { encoding: 'utf8' }
    ).trim();

    if (password && password !== '') {
      // Use the password as the decryption key (Chrome uses PBKDF2)
      const salt = Buffer.from('saltysalt');
      const iterations = 1003;
      const key = crypto.pbkdf2Sync(password, salt, iterations, 16, 'sha1');
      return key;
    }

    throw new Error('Could not access Chrome Safe Storage password');
  } catch (error) {
    console.log('⚠️  Could not get Chrome encryption key:', error.message);
    return null;
  }
}

/**
 * Decrypt Chrome cookie value
 */
function decryptCookieValue(encryptedValue, key) {
  if (!encryptedValue || !key) {
    return null;
  }

  try {
    // Check if the value starts with 'v10' prefix (newer Chrome encryption)
    if (encryptedValue.length < 3) {
      return null;
    }

    const prefix = encryptedValue.slice(0, 3).toString();

    if (prefix === 'v10') {
      // Chrome v10 encryption: AES-128-CBC with 16-byte IV
      if (encryptedValue.length < 19) {
        return null;
      }

      const iv = encryptedValue.slice(3, 19); // 16-byte IV
      const encrypted = encryptedValue.slice(19);

      const decipher = crypto.createDecipheriv('aes-128-cbc', key, iv);
      decipher.setAutoPadding(true);

      let decrypted = decipher.update(encrypted);
      decrypted = Buffer.concat([decrypted, decipher.final()]);

      // Clean up any non-printable characters from the beginning and end
      let result = decrypted.toString('utf8');

      // Remove any leading and trailing binary/non-printable data (common with Chrome decryption)
      result = result.replace(/^[\x00-\x1F\x7F-\x9F]+/, '');
      result = result.replace(/[\x00-\x1F\x7F-\x9F]+$/, '');

      // Extract just the SID value (starts with organization ID like 00D5w000004rH0y!)
      // More flexible pattern to handle various org ID formats
      const sidMatch = result.match(/(00[A-Za-z0-9]{15}![A-Za-z0-9._-]+)/);
      if (sidMatch) {
        result = sidMatch[1];
      } else {
        // Try broader pattern in case format is different
        const broadMatch = result.match(/([A-Za-z0-9]{18}![A-Za-z0-9._-]+)/);
        if (broadMatch) {
          result = broadMatch[1];
        } else {
          // Last resort: find any continuous alphanumeric string that looks like a SID
          const lastResort = result.match(/([A-Za-z0-9!._-]{80,})/);
          if (lastResort) {
            result = lastResort[1];
          }
        }
      }

      return result;
    } else {
      // Older Chrome encryption or unencrypted value
      return encryptedValue.toString('utf8');
    }
  } catch (error) {
    console.log('⚠️  Could not decrypt cookie value:', error.message);
    return null;
  }
}

/**
 * Get Salesforce domain from .env file
 */
function getTargetDomain() {
  try {
    const envPath = path.join(process.cwd(), '.env');
    if (fs.existsSync(envPath)) {
      const envContent = fs.readFileSync(envPath, 'utf8');
      const match = envContent.match(/SALESFORCE_BASE_URL=https:\/\/([^/]+)/);
      if (match && match[1]) {
        return match[1];
      }
    }
  } catch (error) {
    // Ignore error, just return null
  }
  return null;
}

/**
 * Extract Salesforce SID cookie from Chrome on macOS
 * Note: Chrome must be closed for this to work reliably
 */
async function extractSalesforceSID() {
  try {
    // Chrome cookies database path
    const cookiesPath = path.join(
      os.homedir(),
      'Library/Application Support/Google/Chrome/Default/Cookies'
    );

    if (!fs.existsSync(cookiesPath)) {
      throw new Error('Chrome cookies database not found. Make sure Chrome is installed.');
    }

    console.log('🔍 Searching for Salesforce SID cookie...');

    // Get Chrome's encryption key
    console.log('🔑 Getting Chrome encryption key...');
    const encryptionKey = getChromeEncryptionKey();

    // Create a temporary copy of the cookies database (Chrome locks the original)
    const tempCookiesPath = '/tmp/chrome_cookies_temp.db';
    execSync(`cp "${cookiesPath}" "${tempCookiesPath}"`);

    const targetDomain = getTargetDomain();
    if (targetDomain) {
      console.log(`🎯 Target domain from .env: ${targetDomain}`);
    } else {
      console.log('ℹ️  No target domain found in .env, will search for any Salesforce SID');
    }

    // Helper to process query results
    const processResult = (result) => {
      if (!result.trim()) return null;

      const lines = result.trim().split('\n');
      for (const line of lines) {
        const [name, valueOrHex, host, expires] = line.split('|');

        let finalValue = valueOrHex;

        // If it looks like hex (encrypted), try to decrypt
        if (/^[0-9A-Fa-f]+$/.test(valueOrHex) && encryptionKey) {
          try {
            const encryptedValue = Buffer.from(valueOrHex, 'hex');
            const decrypted = decryptCookieValue(encryptedValue, encryptionKey);
            if (decrypted) finalValue = decrypted;
          } catch (e) {
            continue;
          }
        }

        if (finalValue && finalValue.trim() !== '') {
          // Validate SID format
          const sidRegex = /^[a-zA-Z0-9]{15}![a-zA-Z0-9._-]+$/;
          if (sidRegex.test(finalValue)) {
            return {
              name,
              value: finalValue,
              host,
              expires: new Date(parseInt(expires) / 1000)
            };
          }
        }
      }
      return null;
    };

    try {
      // Strategy 1: Look for specific domain if we have one
      if (targetDomain) {
        console.log(`🔎 Searching specifically for ${targetDomain}...`);

        // Note: host_key in Chrome cookies usually starts with . for domain cookies
        const domainQuery = `
          SELECT name, HEX(encrypted_value), host_key, expires_utc
          FROM cookies
          WHERE (host_key = '${targetDomain}' OR host_key = '.${targetDomain}')
          AND (name = 'sid' OR name = 'SID')
          ORDER BY expires_utc DESC
          LIMIT 1;
        `;

        const result = execSync(`sqlite3 "${tempCookiesPath}" "${domainQuery}"`, { encoding: 'utf8' });
        const cookie = processResult(result);
        if (cookie) {
          console.log('✅ Found match for configured domain!');
          console.log(`   Host: ${cookie.host}`);
          console.log(`   Value: ${cookie.value.substring(0, 20)}...`);
        }
      }

      // Strategy 2: Fallback to any Salesforce domain
      console.log('⚠️  Target domain verify failed or not set. Searching all Salesforce cookies...');

      const broadQuery = `
        SELECT name, HEX(encrypted_value), host_key, expires_utc
        FROM cookies
        WHERE host_key LIKE '%salesforce%' 
        AND (name = 'sid' OR name = 'SID' OR name LIKE '%sid%')
        ORDER BY expires_utc DESC;
      `;

      const result = execSync(`sqlite3 "${tempCookiesPath}" "${broadQuery}"`, { encoding: 'utf8' });

      // Clean up temp file
      fs.unlinkSync(tempCookiesPath);

      if (result.trim()) {
        const lines = result.trim().split('\n');
        console.log(`ℹ️  Found ${lines.length} potential candidates. Please review them and pick the correct one.`);

        let bestMatch = null;
        for (const line of lines) {
          const cookie = processResult(line);
          if (cookie) {
            if (!bestMatch) {
              bestMatch = cookie;
            }
            console.log('---');
            console.log(`   Host: ${cookie.host}`);
            console.log(`   Value: ${cookie.value}`);
            console.log(`   Expires: ${cookie.expires}`);
          }
        }

        if (bestMatch) {
          console.log('---');
          console.log('✅ Using the most recent candidate as the best match.');
          console.log(`   Host: ${bestMatch.host}`);
          console.log(`   Value: ${bestMatch.value.substring(0, 20)}...`);
          return bestMatch;
        }
      }

      console.log('❌ No decryptable Salesforce SID cookie found.');
      return null;

    } catch (dbError) {
      if (fs.existsSync(tempCookiesPath)) fs.unlinkSync(tempCookiesPath);
      throw dbError;
    }

  } catch (error) {
    console.error('❌ Error extracting cookie:', error.message);
    return null;
  }
}

/**
 * Update .env file with the extracted SID
 */
function updateEnvFile(sid) {
  const envPath = '.env';

  if (!fs.existsSync(envPath)) {
    console.error('❌ .env file not found');
    return false;
  }

  // Check if SID is valid
  if (!sid || sid.trim() === '') {
    console.error('❌ SID is empty or invalid');
    return false;
  }

  try {
    let envContent = fs.readFileSync(envPath, 'utf8');

    // Update the SID line
    const sidRegex = /^SALESFORCE_SID=.*$/m;
    if (sidRegex.test(envContent)) {
      envContent = envContent.replace(sidRegex, `SALESFORCE_SID=${sid}`);
    } else {
      // Add SID if not present
      envContent += `\nSALESFORCE_SID=${sid}`;
    }

    fs.writeFileSync(envPath, envContent);
    console.log('✅ Updated .env file with new SID');

    // Also update Claude Desktop config file if it exists
    const claudeConfigPath = path.join(os.homedir(), 'Library/Application Support/Claude/claude_desktop_config.json');
    if (fs.existsSync(claudeConfigPath)) {
      try {
        const claudeConfig = JSON.parse(fs.readFileSync(claudeConfigPath, 'utf8'));
        if (claudeConfig.mcpServers?.['salesforce-connector']?.env) {
          claudeConfig.mcpServers['salesforce-connector'].env.SALESFORCE_SID = sid;
          fs.writeFileSync(claudeConfigPath, JSON.stringify(claudeConfig, null, 2));
          console.log('✅ Updated Claude Desktop config with new SID');
        }
      } catch (claudeError) {
        console.log('⚠️  Could not update Claude Desktop config:', claudeError.message);
      }
    }

    return true;
  } catch (error) {
    console.error('❌ Error updating .env file:', error.message);
    return false;
  }
}

// Main execution
async function main() {
  console.log('🚀 Please paste the Salesforce SID and press Enter:');

  const readline = await import('readline');
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  rl.on('line', (sid) => {
    if (sid && sid.trim() !== '') {
      updateEnvFile(sid.trim());
      rl.close();
    } else {
      console.log('❌ SID cannot be empty. Please paste a valid SID.');
    }
  });
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}

export { extractSalesforceSID, updateEnvFile };