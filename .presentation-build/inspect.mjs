import fs from 'node:fs/promises';
import { PresentationFile, FileBlob } from 'file:///C:/Users/babur/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
import { chromium } from 'file:///C:/Users/babur/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs';
const dir = new URL('.', import.meta.url);
const browser = await chromium.launch({headless:true,channel:'msedge',args:['--allow-file-access-from-files']});
const page = await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});
page.on('console',m=>{if(m.type()==='error')console.log('BROWSER',m.text().slice(0,120))});
for (const name of ['dashboard','directory','workspace','wallet','notifications','certificate']) {
 await page.goto(new URL(name+'.html',dir).href,{waitUntil:'load'});
 await page.waitForTimeout(1000);
 await page.screenshot({path:new URL(name+'.png',dir).pathname.slice(1),fullPage:true});
 console.log('CAPTURED',name,await page.title());
}
await browser.close();
