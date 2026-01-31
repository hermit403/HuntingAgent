const vm = require('vm');

async function main() {
    let buffer = '';
    process.stdin.on('data', (chunk) => buffer += chunk);
    process.stdin.on('end', () => {
        const logs = [];
        const capture = (...args) => {
            logs.push(args.map(a => 
                (typeof a === 'object' && a !== null) ? JSON.stringify(a) : String(a)
            ).join(' '));
        };
        const originalLog = console.log;
        const originalError = console.error;
        const originalWarn = console.warn;
        console.log = capture;
        console.error = capture;
        console.warn = capture;
        try {
            const req = JSON.parse(buffer);
            const result = vm.runInNewContext(req.code, {}, { timeout: 5000 });
            console.log = originalLog;
            console.error = originalError;
            console.warn = originalWarn;
            let finalOutput = result;
            if (logs.length > 0) {
                const logStr = logs.join('\n');
                if (result === undefined) {
                    finalOutput = logStr;
                } else {
                    finalOutput = `Logs:\n${logStr}\nResult: ${result}`;
                }
            }
            process.stdout.write(JSON.stringify({ result: finalOutput }));
        } catch (e) {
            console.log = originalLog;
            console.error = originalError;
            console.warn = originalWarn;
            process.stdout.write(JSON.stringify({ error: e.message || String(e) }));
        }
    });
}

main();
