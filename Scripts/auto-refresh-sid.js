import { extractSalesforceSID } from './extract-sid.js';
import fs from 'fs';
import path from 'path';
import os from 'os';

async function refresh() {
    console.log('Attempting to extract SID from Chrome...');
    const cookie = await extractSalesforceSID();

    if (cookie && cookie.value) {
        console.log('Found SID for host:', cookie.host);

        const mcpConfigPath = '/Users/santiagot/.gemini/antigravity/mcp_config.json';
        if (fs.existsSync(mcpConfigPath)) {
            const config = JSON.parse(fs.readFileSync(mcpConfigPath, 'utf8'));
            if (config.mcpServers && config.mcpServers['salesforce-connector']) {
                config.mcpServers['salesforce-connector'].env.SALESFORCE_SID = cookie.value;
                fs.writeFileSync(mcpConfigPath, JSON.stringify(config, null, 4));
                console.log('Updated mcp_config.json');
            }
        }

        // Also update .env in the connector dir
        const envPath = './.env';
        if (fs.existsSync(envPath)) {
            let envContent = fs.readFileSync(envPath, 'utf8');
            const sidRegex = /^SALESFORCE_SID=.*$/m;
            if (sidRegex.test(envContent)) {
                envContent = envContent.replace(sidRegex, `SALESFORCE_SID=${cookie.value}`);
            } else {
                envContent += `\nSALESFORCE_SID=${cookie.value}`;
            }
            fs.writeFileSync(envPath, envContent);
            console.log('Updated .env');
        }

        console.log('Successfully refreshed Salesforce SID.');
    } else {
        console.error('Failed to extract SID. Make sure you are logged into Salesforce in Chrome and Chrome is not strictly locking the database.');
        process.exit(1);
    }
}

refresh().catch(console.error);
