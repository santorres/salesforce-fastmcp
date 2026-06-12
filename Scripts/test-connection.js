#!/usr/bin/env node

/**
 * Quick connection test for Salesforce MCP Connector.
 * Tests Bearer token authentication and basic API connectivity.
 * 
 * Usage:
 *   export SALESFORCE_BASE_URL="https://your-instance.salesforce.com"
 *   export SALESFORCE_ACCESS_TOKEN="your-token-here"
 *   node test-connection.js
 */

import axios from 'axios';
import dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
dotenv.config({ path: join(__dirname, '..', '.env') });

const BASE_URL = process.env.SALESFORCE_BASE_URL;
const ACCESS_TOKEN = process.env.SALESFORCE_ACCESS_TOKEN || process.env.SALESFORCE_SID;

if (!BASE_URL || !ACCESS_TOKEN) {
  console.error('❌ Missing required environment variables:');
  console.error('   SALESFORCE_BASE_URL and SALESFORCE_ACCESS_TOKEN (or SALESFORCE_SID)');
  console.error('\nSet them before running:');
  console.error('   export SALESFORCE_BASE_URL="https://your-instance.salesforce.com"');
  console.error('   export SALESFORCE_ACCESS_TOKEN="your-token-here"');
  process.exit(1);
}

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Authorization': `Bearer ${ACCESS_TOKEN}`,
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

async function testConnection() {
  console.log('🔍 Testing Salesforce connection...\n');
  console.log(`   Base URL: ${BASE_URL}`);
  console.log(`   Token: ${ACCESS_TOKEN.substring(0, 20)}...\n`);

  try {
    // Test 1: Identity endpoint
    console.log('📌 Test 1: Checking identity endpoint...');
    const identityRes = await api.get('/services/oauth2/token');
    console.log('   ✅ Identity endpoint reachable\n');

    // Test 2: Query basic data
    console.log('📌 Test 2: Querying Accounts...');
    const queryRes = await api.get('/services/data/v60.0/query', {
      params: { q: "SELECT Id, Name FROM Account LIMIT 5" }
    });
    
    const accounts = queryRes.data.records;
    console.log(`   ✅ Query successful - Found ${accounts.length} accounts`);
    if (accounts.length > 0) {
      console.log('   Sample accounts:');
      accounts.slice(0, 3).forEach(acc => {
        console.log(`      - ${acc.Name} (${acc.Id})`);
      });
    }
    console.log('');

    // Test 3: Check Opportunities with Partner fields
    console.log('📌 Test 3: Checking Partner__r relationship...');
    const oppRes = await api.get('/services/data/v60.0/query', {
      params: { 
        q: "SELECT Id, Name, Partner__r.Name FROM Opportunity WHERE Partner__r.Name != null LIMIT 3" 
      }
    });
    
    const opportunities = oppRes.data.records;
    console.log(`   ✅ Partner relationship query successful - Found ${opportunities.length} opportunities`);
    if (opportunities.length > 0) {
      opportunities.forEach(opp => {
        console.log(`      - ${opp.Name} (Partner: ${opp.Partner__r?.Name || 'N/A'})`);
      });
    }
    console.log('');

    console.log('✅ All tests passed! Your Bearer token is working correctly.\n');
    console.log('🚀 You can now run the MCP inspector:');
    console.log('   npx @modelcontextprotocol/inspector node server.js\n');

  } catch (error) {
    console.error('❌ Connection test failed!\n');
    
    if (error.response) {
      console.error(`   Status: ${error.response.status}`);
      console.error(`   Message: ${error.response.data?.message || error.response.statusText}`);
      
      if (error.response.status === 401) {
        console.error('\n   💡 Token may be invalid or expired.');
        console.error('      Try refreshing your session ID or access token.');
      }
    } else if (error.code === 'ECONNREFUSED') {
      console.error('   Cannot connect to Salesforce instance.');
      console.error('   Check your SALESFORCE_BASE_URL is correct.');
    } else {
      console.error(`   Error: ${error.message}`);
    }
    
    process.exit(1);
  }
}

testConnection();
