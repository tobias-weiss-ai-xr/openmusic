import { test, expect, describe, vi, beforeEach, afterEach } from 'vitest';
import { mkdirSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';

const TEST_DIR = join(tmpdir(), 'openmusic-cli-test');

beforeEach(() => {
  mkdirSync(TEST_DIR, { recursive: true });
});

afterEach(() => {
  rmSync(TEST_DIR, { recursive: true, force: true });
  vi.restoreAllMocks();
});

describe('CLI entry point', () => {
  async function runCliWithArgs(args: string[]): Promise<{ exitCode: number; stderr: string[] }> {
    const stderrMessages: string[] = [];

    const exitMock = vi.spyOn(process, 'exit').mockImplementation((code?: string | number | null) => {
      throw new Error(`__CLI_EXIT__${code}__`);
    });

    const stderrSpy = vi.spyOn(process.stderr, 'write').mockImplementation((str: string | Uint8Array) => {
      stderrMessages.push(String(str));
      return true as any;
    });

    const origArgv1 = process.argv[1];
    process.argv[1] = '/some/path/dist/index.js';

    const origArgvRest = process.argv.slice(2);
    process.argv.splice(2, process.argv.length - 2, ...args);

    vi.resetModules();

    try {
      await import('./index.js');
    } catch (e: unknown) {
      if (e instanceof Error && e.message.startsWith('__CLI_EXIT__')) {
        const code = parseInt(e.message.replace('__CLI_EXIT__', '').replace('__', ''));
        return { exitCode: code, stderr: stderrMessages };
      }
      throw e;
    } finally {
      process.argv[1] = origArgv1;
      process.argv.splice(2, process.argv.length - 2, ...origArgvRest);
      exitMock.mockRestore();
      stderrSpy.mockRestore();
    }

    return { exitCode: 0, stderr: stderrMessages };
  }

  test('exits with code 1 when --config is missing', async () => {
    const result = await runCliWithArgs([]);

    expect(result.exitCode).toBe(1);
    expect(result.stderr.some((m) => m.includes('Usage'))).toBe(true);
  });

  test('exits with code 1 when config file does not exist', async () => {
    const result = await runCliWithArgs(['--config', '/nonexistent/config.json']);

    expect(result.exitCode).toBe(1);
    expect(result.stderr.some((m) => m.includes('not found'))).toBe(true);
  });
});
