#!/usr/bin/env node

import readline from 'readline';

const BASE_URL = 'https://semperis.my.salesforce.com/services/data/v62.0';

async function testToken(token) {
  try {
    const response = await fetch(`${BASE_URL}/query?q=SELECT+Id+FROM+Account+LIMIT+1`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    const data = await response.json();

    if (response.ok) {
      console.log('\n✓ Token is VALID');
      console.log(`  Found ${data.totalSize} record(s)`);
      return true;
    } else {
      console.log('\n✗ Token is INVALID or EXPIRED');
      console.log(`  Error: ${data[0]?.message || JSON.stringify(data)}`);
      return false;
    }
  } catch (error) {
    console.log('\n✗ Connection failed');
    console.log(`  Error: ${error.message}`);
    return false;
  }
}

// Check if token passed as argument
const argToken = process.argv[2];

if (argToken) {
  testToken(argToken);
} else {
  // Prompt for token
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });

  rl.question('Paste your Salesforce SID token: ', async (token) => {
    rl.close();
    await testToken(token.trim());
  });
}
