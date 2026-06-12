
import { spawn } from 'child_process';
import { setTimeout } from 'timers/promises';

async function fetchPartners() {
    console.log('🚀 Starting MCP server...');

    const server = spawn('node', ['server.js'], {
        stdio: ['pipe', 'pipe', 'pipe']
    });

    let serverReady = false;

    server.stderr.on('data', (data) => {
        const output = data.toString();
        if (output.includes('Salesforce MCP server running')) {
            serverReady = true;
        }
    });

    // Wait for server
    for (let i = 0; i < 20; i++) {
        if (serverReady) break;
        await setTimeout(500);
    }

    if (!serverReady) {
        console.error('❌ Server failed to start');
        server.kill();
        process.exit(1);
    }

    console.log('✅ Server ready. Querying Partners in Italy...');

    const query = `SELECT Id, Name, Type, BillingCity, BillingState, Phone, Website FROM Account WHERE BillingCountry = 'Italy' AND (Type LIKE '%Partner%' OR Type = 'Channel Partner / Reseller' OR Type = 'Reseller') LIMIT 20`;

    const request = {
        jsonrpc: '2.0',
        id: 1,
        method: 'tools/call',
        params: {
            name: 'salesforce_query',
            arguments: {
                q: query
            }
        }
    };

    const requestStr = JSON.stringify(request) + '\n';
    server.stdin.write(requestStr);

    let buffer = '';
    server.stdout.on('data', (data) => {
        buffer += data.toString();
        const lines = buffer.split('\n');

        for (const line of lines) {
            if (!line.trim()) continue;
            try {
                const response = JSON.parse(line);
                if (response.id === 1) {
                    if (response.error) {
                        console.error('❌ Query error:', response.error);
                    } else {
                        const content = response.result.content[0].text;
                        console.log('\n🇮🇹 Partners in Italy:');
                        console.log(content);
                    }
                    server.kill();
                    process.exit(0);
                }
            } catch (e) {
                // incomplete json
            }
        }
    });
}

fetchPartners().catch(console.error);
