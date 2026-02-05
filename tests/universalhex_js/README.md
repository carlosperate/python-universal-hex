# JavaScript for the original microbit-universal-hex library

This directory contains a bundled JavaScript version of the original
microbit-universal-hex TypeScript library for comparison testing with the
Python port.

## Version

Source: https://github.com/microbit-foundation/microbit-universal-hex
Version: v0.2.2
Commit: be728548588c07b85066ad0e1b8bd535ddacdec3

## How to build the JS file

```bash
git clone https://github.com/microbit-foundation/microbit-universal-hex.git
cd microbit-universal-hex
npm install
npm run build
npx esbuild src/index.ts --bundle --outfile=microbit-universal-hex.js --format=iife --global-name=universalHex
```

## microbit-universal-hex License

MIT License

Copyright (c) 2020 Micro:bit Educational Foundation

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
