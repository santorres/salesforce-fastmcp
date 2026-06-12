#!/usr/bin/env node

import { spawn } from 'child_process';
import { setTimeout } from 'timers/promises';

class MCPTester {
  constructor() {
    this.server = null;
    this.requestId = 1;
  }

  async startServer() {
    console.log('🚀 Starting MCP server...');
    
    this.server = spawn('node', ['server.js'], {
      stdio: ['pipe', 'pipe', 'pipe']
    });

    let serverReady = false;
    
    this.server.stderr.on('data', (data) => {
      const output = data.toString();
      if (output.includes('Salesforce MCP server running on stdio')) {
        serverReady = true;
      }
    });

    // Wait for server to be ready
    let attempts = 0;
    while (!serverReady && attempts < 10) {
      await setTimeout(200);
      attempts++;
    }

    if (!serverReady) {
      throw new Error('Server failed to start within timeout');
    }

    console.log('✅ MCP server started successfully\n');
    return true;
  }

  async sendMCPRequest(method, params = {}) {
    const request = {
      jsonrpc: '2.0',
      id: this.requestId++,
      method,
      params
    };

    const requestStr = JSON.stringify(request) + '\n';
    
    return new Promise((resolve, reject) => {
      let responseData = '';
      let timeoutId;

      const onData = (data) => {
        responseData += data.toString();
        
        // Look for complete JSON response
        try {
          const lines = responseData.split('\n').filter(line => line.trim());
          for (const line of lines) {
            const response = JSON.parse(line);
            if (response.id === request.id) {
              clearTimeout(timeoutId);
              this.server.stdout.off('data', onData);
              resolve(response);
              return;
            }
          }
        } catch (e) {
          // Continue collecting data
        }
      };

      this.server.stdout.on('data', onData);
      
      // Set timeout
      timeoutId = global.setTimeout(() => {
        this.server.stdout.off('data', onData);
        reject(new Error(`Request timeout for method: ${method}`));
      }, 10000);

      // Send request
      this.server.stdin.write(requestStr);
    });
  }

  async testListTools() {
    console.log('📋 Testing tools/list...');
    
    try {
      const response = await this.sendMCPRequest('tools/list');
      
      if (response.error) {
        console.log('❌ tools/list failed:', response.error.message);
        return false;
      }

      const tools = response.result?.tools || [];
      const expectedTools = ['salesforce_query', 'salesforce_sobjects', 'salesforce_recent'];
      
      console.log(`✅ Found ${tools.length} tools:`);
      tools.forEach(tool => {
        console.log(`   - ${tool.name}: ${tool.description}`);
      });

      const hasAllTools = expectedTools.every(expectedTool => 
        tools.some(tool => tool.name === expectedTool)
      );

      if (hasAllTools) {
        console.log('✅ All expected tools are available\n');
        return true;
      } else {
        console.log('❌ Some expected tools are missing\n');
        return false;
      }
    } catch (error) {
      console.log('❌ tools/list error:', error.message);
      return false;
    }
  }

  async testTool(toolName, args = {}) {
    console.log(`🔧 Testing ${toolName}...`);
    
    try {
      const response = await this.sendMCPRequest('tools/call', {
        name: toolName,
        arguments: args
      });

      if (response.error) {
        console.log(`❌ ${toolName} failed:`, response.error.message);
        return false;
      }

      const content = response.result?.content?.[0]?.text;
      if (content) {
        try {
          const data = JSON.parse(content);
          console.log(`✅ ${toolName} returned data:`, typeof data, Object.keys(data).slice(0, 3));
        } catch (e) {
          console.log(`✅ ${toolName} returned text (${content.length} chars)`);
        }
      } else {
        console.log(`⚠️  ${toolName} returned no content`);
      }
      
      return true;
    } catch (error) {
      console.log(`❌ ${toolName} error:`, error.message);
      return false;
    }
  }

  async runAllTests() {
    const results = {
      serverStart: false,
      listTools: false,
      query: false,
      sobjects: false,
      recent: false
    };

    try {
      // Start server
      results.serverStart = await this.startServer();

      // Test list tools
      results.listTools = await this.testListTools();

      // Test individual tools
      results.query = await this.testTool('salesforce_query', { 
        q: 'SELECT Id FROM Account LIMIT 1' 
      });
      
      results.sobjects = await this.testTool('salesforce_sobjects');
      
      results.recent = await this.testTool('salesforce_recent', { 
        limit: 5 
      });

    } catch (error) {
      console.error('Test suite error:', error);
    } finally {
      // Clean up
      if (this.server) {
        this.server.kill('SIGTERM');
      }
    }

    return results;
  }

  printSummary(results) {
    console.log('\n' + '='.repeat(50));
    console.log('📊 MCP SERVER TEST RESULTS');
    console.log('='.repeat(50));
    
    const tests = [
      ['Server Startup', results.serverStart],
      ['List Tools', results.listTools], 
      ['Salesforce Query', results.query],
      ['Salesforce SObjects', results.sobjects],
      ['Salesforce Recent', results.recent]
    ];

    tests.forEach(([name, passed]) => {
      console.log(`${passed ? '✅' : '❌'} ${name}`);
    });

    const passedCount = Object.values(results).filter(Boolean).length;
    const totalCount = Object.keys(results).length;
    
    console.log(`\n📈 Summary: ${passedCount}/${totalCount} tests passed`);
    
    if (passedCount === totalCount) {
      console.log('🎉 All tests passed! Your Salesforce MCP connector is working perfectly!');
    } else {
      console.log('⚠️  Some tests failed. Check the logs above for details.');
    }
  }
}

// Run tests
async function main() {
  const tester = new MCPTester();
  const results = await tester.runAllTests();
  tester.printSummary(results);
  
  process.exit(Object.values(results).every(Boolean) ? 0 : 1);
}

main().catch(console.error);