#!/usr/bin/env node

import { spawn } from 'child_process';
import readline from 'readline';

class InteractiveMCPTester {
  constructor() {
    this.server = null;
    this.requestId = 1;
    this.rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
  }

  async startServer() {
    console.log('🚀 Starting Salesforce MCP Server...\n');
    
    this.server = spawn('node', ['server.js'], {
      stdio: ['pipe', 'pipe', 'pipe']
    });

    let serverReady = false;
    
    this.server.stderr.on('data', (data) => {
      const output = data.toString();
      if (output.includes('Salesforce MCP server running on stdio')) {
        console.log('✅ Server is running and ready!\n');
        serverReady = true;
        this.showMenu();
      }
    });

    this.server.on('error', (error) => {
      console.error('❌ Server error:', error);
    });

    // Wait for server to start
    await new Promise((resolve) => {
      const checkReady = () => {
        if (serverReady) {
          resolve();
        } else {
          setTimeout(checkReady, 100);
        }
      };
      checkReady();
    });
  }

  showMenu() {
    console.log('🔧 Available Tests:');
    console.log('==================');
    console.log('1. List all available tools');
    console.log('2. Query Salesforce (custom SOQL)');
    console.log('3. Get all Salesforce objects');
    console.log('4. Get recent records');
    console.log('5. Quick Account query');
    console.log('6. Quick Opportunity query');
    console.log('0. Exit');
    console.log();
    
    this.promptUser();
  }

  promptUser() {
    this.rl.question('Choose an option (0-6): ', (answer) => {
      this.handleChoice(answer.trim());
    });
  }

  async handleChoice(choice) {
    console.log();
    
    switch (choice) {
      case '1':
        await this.listTools();
        break;
      case '2':
        await this.customQuery();
        break;
      case '3':
        await this.getSObjects();
        break;
      case '4':
        await this.getRecent();
        break;
      case '5':
        await this.quickAccountQuery();
        break;
      case '6':
        await this.quickOpportunityQuery();
        break;
      case '0':
        this.cleanup();
        return;
      default:
        console.log('❌ Invalid choice. Please try again.\n');
        this.showMenu();
        return;
    }
    
    console.log('\n' + '='.repeat(50) + '\n');
    this.showMenu();
  }

  async sendRequest(method, params = {}) {
    const request = {
      jsonrpc: '2.0',
      id: this.requestId++,
      method,
      params
    };

    return new Promise((resolve, reject) => {
      let responseBuffer = '';
      
      const onData = (data) => {
        responseBuffer += data.toString();
        try {
          const response = JSON.parse(responseBuffer.trim());
          if (response.id === request.id) {
            this.server.stdout.off('data', onData);
            resolve(response);
          }
        } catch (e) {
          // Continue collecting data
        }
      };

      this.server.stdout.on('data', onData);
      
      // Send request
      this.server.stdin.write(JSON.stringify(request) + '\n');
      
      // Timeout after 10 seconds
      setTimeout(() => {
        this.server.stdout.off('data', onData);
        reject(new Error('Request timeout'));
      }, 10000);
    });
  }

  async listTools() {
    console.log('📋 Listing available tools...');
    
    try {
      const response = await this.sendRequest('tools/list');
      
      if (response.result?.tools) {
        console.log(`✅ Found ${response.result.tools.length} tools:`);
        response.result.tools.forEach((tool, index) => {
          console.log(`\n${index + 1}. ${tool.name}`);
          console.log(`   Description: ${tool.description}`);
          if (tool.inputSchema?.properties) {
            console.log(`   Parameters: ${Object.keys(tool.inputSchema.properties).join(', ')}`);
          }
        });
      } else {
        console.log('❌ No tools found');
      }
    } catch (error) {
      console.log('❌ Error:', error.message);
    }
  }

  async customQuery() {
    return new Promise((resolve) => {
      this.rl.question('Enter SOQL query: ', async (query) => {
        console.log(`\n🔍 Executing: ${query}`);
        
        try {
          const response = await this.sendRequest('tools/call', {
            name: 'salesforce_query',
            arguments: { q: query }
          });
          
          if (response.result?.content?.[0]?.text) {
            const result = JSON.parse(response.result.content[0].text);
            console.log('✅ Query Results:');
            console.log(`   Total Size: ${result.totalSize}`);
            console.log(`   Records: ${result.records?.length || 0}`);
            
            if (result.records?.length > 0) {
              console.log('\n   Sample Record:');
              console.log('   ' + JSON.stringify(result.records[0], null, 2).replace(/\n/g, '\n   '));
            }
          } else if (response.result?.content?.[0]?.text?.includes('Error')) {
            console.log('❌ Query Error:', response.result.content[0].text);
          } else {
            console.log('⚠️  Unexpected response format');
          }
        } catch (error) {
          console.log('❌ Error:', error.message);
        }
        
        resolve();
      });
    });
  }

  async getSObjects() {
    console.log('📊 Getting Salesforce objects...');
    
    try {
      const response = await this.sendRequest('tools/call', {
        name: 'salesforce_sobjects',
        arguments: {}
      });
      
      if (response.result?.content?.[0]?.text) {
        const result = JSON.parse(response.result.content[0].text);
        console.log('✅ Salesforce Objects:');
        console.log(`   Total Objects: ${result.sobjects?.length || 0}`);
        
        if (result.sobjects?.length > 0) {
          console.log('\n   Sample Objects:');
          result.sobjects.slice(0, 5).forEach(obj => {
            console.log(`   - ${obj.name} (${obj.label})`);
          });
          
          if (result.sobjects.length > 5) {
            console.log(`   ... and ${result.sobjects.length - 5} more`);
          }
        }
      } else {
        console.log('❌ No objects returned');
      }
    } catch (error) {
      console.log('❌ Error:', error.message);
    }
  }

  async getRecent() {
    console.log('📈 Getting recent records...');
    
    try {
      const response = await this.sendRequest('tools/call', {
        name: 'salesforce_recent',
        arguments: { limit: 10 }
      });
      
      if (response.result?.content?.[0]?.text) {
        const result = JSON.parse(response.result.content[0].text);
        console.log('✅ Recent Records:');
        
        if (result.length > 0) {
          result.forEach((record, index) => {
            console.log(`   ${index + 1}. ${record.Name || record.attributes?.type || 'Unknown'}`);
          });
        } else {
          console.log('   No recent records found');
        }
      } else {
        console.log('❌ No recent records returned');
      }
    } catch (error) {
      console.log('❌ Error:', error.message);
    }
  }

  async quickAccountQuery() {
    console.log('👥 Quick Account Query...');
    
    try {
      const response = await this.sendRequest('tools/call', {
        name: 'salesforce_query',
        arguments: { q: 'SELECT Id, Name, Type, Industry FROM Account LIMIT 5' }
      });
      
      if (response.result?.content?.[0]?.text) {
        const result = JSON.parse(response.result.content[0].text);
        console.log('✅ Account Results:');
        console.log(`   Total Accounts: ${result.totalSize}`);
        
        if (result.records?.length > 0) {
          result.records.forEach((account, index) => {
            console.log(`   ${index + 1}. ${account.Name} (${account.Type || 'No Type'}) - ${account.Industry || 'No Industry'}`);
          });
        }
      } else {
        console.log('❌ No accounts returned');
      }
    } catch (error) {
      console.log('❌ Error:', error.message);
    }
  }

  async quickOpportunityQuery() {
    console.log('💰 Quick Opportunity Query...');
    
    try {
      const response = await this.sendRequest('tools/call', {
        name: 'salesforce_query',
        arguments: { q: 'SELECT Id, Name, StageName, Amount FROM Opportunity LIMIT 5' }
      });
      
      if (response.result?.content?.[0]?.text) {
        const result = JSON.parse(response.result.content[0].text);
        console.log('✅ Opportunity Results:');
        console.log(`   Total Opportunities: ${result.totalSize}`);
        
        if (result.records?.length > 0) {
          result.records.forEach((opp, index) => {
            console.log(`   ${index + 1}. ${opp.Name} - ${opp.StageName} ($${opp.Amount || '0'})`);
          });
        }
      } else {
        console.log('❌ No opportunities returned');
      }
    } catch (error) {
      console.log('❌ Error:', error.message);
    }
  }

  cleanup() {
    console.log('\n🧹 Shutting down...');
    this.rl.close();
    
    if (this.server) {
      this.server.kill('SIGTERM');
    }
    
    console.log('👋 Thanks for testing the Salesforce MCP Connector!');
    process.exit(0);
  }
}

// Start the interactive tester
const tester = new InteractiveMCPTester();
tester.startServer().catch(console.error);