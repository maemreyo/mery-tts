/**
 * Minimal Node.js client for the Mery OpenAI-compatible raw PCM stream.
 *
 * Streams a synthesis request to a WAV file. Uses only Node.js built-ins —
 * no third-party dependencies required.
 *
 * Usage:
 *   node node_client.js \
 *     --url http://127.0.0.1:8765 \
 *     --token <auth_token> \
 *     --model kokoro \
 *     --voice af_heart \
 *     --text "Streaming raw PCM is fast and boring." \
 *     --output out.wav
 */

"use strict";

const fs = require("node:fs");
const http = require("node:http");
const https = require("node:https");
const { URL } = require("node:url");

function parseArgs(argv) {
  const args = { url: "http://127.0.0.1:8765", output: "out.wav" };
  for (let i = 2; i < argv.length; i += 2) {
    const key = argv[i].replace(/^--/, "");
    args[key] = argv[i + 1];
  }
  return args;
}

function parseContentType(contentType) {
  const match = /audio\/L16;rate=(\d+);channels=(\d+)/.exec(contentType || "");
  if (match === null) {
    throw new Error(`unsupported Content-Type for raw PCM: ${contentType}`);
  }
  return {
    sampleRate: Number(match[1]),
    channels: Number(match[2]),
    sampleWidthBytes: 2,
  };
}

function buildWavHeader(format, pcmByteLength) {
  const header = Buffer.alloc(44);
  const byteRate = format.sampleRate * format.channels * format.sampleWidthBytes;
  const blockAlign = format.channels * format.sampleWidthBytes;

  header.write("RIFF", 0);
  header.writeUInt32LE(36 + pcmByteLength, 4);
  header.write("WAVE", 8);
  header.write("fmt ", 12);
  header.writeUInt32LE(16, 16);
  header.writeUInt16LE(1, 20);
  header.writeUInt16LE(format.channels, 22);
  header.writeUInt32LE(format.sampleRate, 24);
  header.writeUInt32LE(byteRate, 28);
  header.writeUInt16LE(blockAlign, 32);
  header.writeUInt16LE(format.sampleWidthBytes * 8, 34);
  header.write("data", 36);
  header.writeUInt32LE(pcmByteLength, 40);
  return header;
}

function fetchJson(url, token) {
  return new Promise((resolve, reject) => {
    const lib = url.protocol === "https:" ? https : http;
    const req = lib.request(
      url,
      { method: "GET", headers: { Authorization: `Bearer ${token}` } },
      (res) => {
        const chunks = [];
        res.on("data", (chunk) => chunks.push(chunk));
        res.on("end", () => {
          const raw = Buffer.concat(chunks).toString("utf-8");
          if (res.statusCode !== 200) {
            reject(new Error(`HTTP ${res.statusCode}: ${raw}`));
            return;
          }
          resolve(JSON.parse(raw));
        });
      },
    );
    req.on("error", reject);
    req.end();
  });
}

function fetchVoiceCapability({ baseUrl, token, voiceId }) {
  return fetchJson(new URL("/v1/voices/installed", baseUrl), token).then(
    (payload) => {
      const match = payload.voices.find((v) => v.voice_id === voiceId);
      return match ? match.streaming : null;
    },
  );
}

function streamSpeechToWav({ baseUrl, token, model, voice, text, outputPath }) {
  return new Promise((resolve, reject) => {
    const url = new URL("/v1/audio/speech", baseUrl);
    const lib = url.protocol === "https:" ? https : http;
    const body = JSON.stringify({
      model,
      voice,
      input: text,
      response_format: "pcm",
      stream_format: "pcm",
    });

    const req = lib.request(
      url,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(body),
        },
      },
      (res) => {
        if (res.statusCode !== 200) {
          const chunks = [];
          res.on("data", (chunk) => chunks.push(chunk));
          res.on("end", () => {
            const raw = Buffer.concat(chunks).toString("utf-8");
            let payload;
            try {
              payload = JSON.parse(raw);
            } catch {
              payload = { code: "unknown", sanitized_diagnostic: raw };
            }
            reject(
              new Error(
                `synthesis rejected (${res.statusCode}): ${payload.code}: ${payload.sanitized_diagnostic}`,
              ),
            );
          });
          return;
        }

        const contentType = res.headers["content-type"] || "";
        const format = parseContentType(contentType);
        const requestId = res.headers["x-mery-request-id"] || "<unknown>";
        const encoding = res.headers["x-mery-audio-encoding"] || "<unknown>";
        process.stderr.write(
          `streaming: content_type=${contentType} request_id=${requestId} encoding=${encoding} sample_rate=${format.sampleRate} channels=${format.channels}\n`,
        );

        const pcmChunks = [];
        let totalLength = 0;
        res.on("data", (chunk) => {
          pcmChunks.push(chunk);
          totalLength += chunk.length;
        });
        res.on("end", () => {
          const pcm = Buffer.concat(pcmChunks, totalLength);
          const header = buildWavHeader(format, pcm.length);
          fs.writeFileSync(outputPath, Buffer.concat([header, pcm]));
          resolve(format);
        });
        res.on("error", reject);
      },
    );
    req.on("error", reject);
    req.write(body);
    req.end();
  });
}

async function main() {
  const args = parseArgs(process.argv);

  if (!args.token || !args.model || !args.voice || !args.text) {
    process.stderr.write(
      "missing required --token, --model, --voice, or --text\n",
    );
    process.exit(2);
  }

  const capability = await fetchVoiceCapability({
    baseUrl: args.url,
    token: args.token,
    voiceId: args.voice,
  });
  if (capability === null || capability === undefined) {
    process.stderr.write(`voice ${args.voice} is not installed\n`);
    process.exit(2);
  }
  if (!capability.supported) {
    process.stderr.write(
      `voice ${args.voice} does not support streaming in P1\n`,
    );
    process.exit(2);
  }

  const format = await streamSpeechToWav({
    baseUrl: args.url,
    token: args.token,
    model: args.model,
    voice: args.voice,
    text: args.text,
    outputPath: args.output,
  });
  process.stdout.write(
    `wrote ${args.output}: ${format.sampleRate} Hz, ${format.channels}ch, ${format.sampleWidthBytes * 8}-bit\n`,
  );
}

main().catch((err) => {
  process.stderr.write(`error: ${err.message}\n`);
  process.exit(1);
});
