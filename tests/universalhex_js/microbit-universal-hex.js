"use strict";
var universalHex = (() => {
  var __defProp = Object.defineProperty;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __export = (target, all) => {
    for (var name in all)
      __defProp(target, name, { get: all[name], enumerable: true });
  };
  var __copyProps = (to, from, except, desc) => {
    if (from && typeof from === "object" || typeof from === "function") {
      for (let key of __getOwnPropNames(from))
        if (!__hasOwnProp.call(to, key) && key !== except)
          __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
    }
    return to;
  };
  var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

  // src/index.ts
  var index_exports = {};
  __export(index_exports, {
    createUniversalHex: () => createUniversalHex,
    iHexToCustomFormatBlocks: () => iHexToCustomFormatBlocks,
    iHexToCustomFormatSection: () => iHexToCustomFormatSection,
    isMakeCodeForV1Hex: () => isMakeCodeForV1Hex,
    isUniversalHex: () => isUniversalHex,
    microbitBoardId: () => microbitBoardId,
    separateUniversalHex: () => separateUniversalHex
  });

  // src/utils.ts
  function hexStrToBytes(hexStr) {
    if (hexStr.length % 2 !== 0) {
      throw new Error(`Hex string "${hexStr}" is not divisible by 2.`);
    }
    const byteArray = hexStr.match(/.{1,2}/g);
    if (byteArray) {
      return new Uint8Array(
        byteArray.map((byteStr) => {
          const byteNum = parseInt(byteStr, 16);
          if (Number.isNaN(byteNum)) {
            throw new Error(`There were some non-hex characters in "${hexStr}".`);
          } else {
            return byteNum;
          }
        })
      );
    } else {
      return new Uint8Array();
    }
  }
  function byteToHexStrFast(byte) {
    return byte.toString(16).toUpperCase().padStart(2, "0");
  }
  function byteArrayToHexStr(byteArray) {
    return byteArray.reduce(
      (accumulator, current) => accumulator + current.toString(16).toUpperCase().padStart(2, "0"),
      ""
    );
  }
  function concatUint8Arrays(arraysToConcat) {
    const fullLength = arraysToConcat.reduce(
      (accumulator, currentValue) => accumulator + currentValue.length,
      0
    );
    const combined = new Uint8Array(fullLength);
    arraysToConcat.reduce((accumulator, currentArray) => {
      combined.set(currentArray, accumulator);
      return accumulator + currentArray.length;
    }, 0);
    return combined;
  }

  // src/ihex.ts
  var RECORD_DATA_MAX_BYTES = 32;
  var START_CODE_STR = ":";
  var START_CODE_INDEX = 0;
  var START_CODE_STR_LEN = START_CODE_STR.length;
  var BYTE_COUNT_STR_INDEX = START_CODE_INDEX + START_CODE_STR_LEN;
  var BYTE_COUNT_STR_LEN = 2;
  var ADDRESS_STR_INDEX = BYTE_COUNT_STR_INDEX + BYTE_COUNT_STR_LEN;
  var ADDRESS_STR_LEN = 4;
  var RECORD_TYPE_STR_INDEX = ADDRESS_STR_INDEX + ADDRESS_STR_LEN;
  var RECORD_TYPE_STR_LEN = 2;
  var DATA_STR_INDEX = RECORD_TYPE_STR_INDEX + RECORD_TYPE_STR_LEN;
  var DATA_STR_LEN_MIN = 0;
  var CHECKSUM_STR_LEN = 2;
  var MIN_RECORD_STR_LEN = START_CODE_STR_LEN + BYTE_COUNT_STR_LEN + ADDRESS_STR_LEN + RECORD_TYPE_STR_LEN + DATA_STR_LEN_MIN + CHECKSUM_STR_LEN;
  var MAX_RECORD_STR_LEN = MIN_RECORD_STR_LEN - DATA_STR_LEN_MIN + RECORD_DATA_MAX_BYTES * 2;
  function isRecordTypeValid(recordType) {
    if (recordType >= 0 /* Data */ && recordType <= 5 /* StartLinearAddress */ || recordType >= 10 /* BlockStart */ && recordType <= 14 /* OtherData */) {
      return true;
    }
    return false;
  }
  function calcChecksumByte(dataBytes) {
    const sum = dataBytes.reduce(
      (accumulator, currentValue) => accumulator + currentValue,
      0
    );
    return -sum & 255;
  }
  function createRecord(address, recordType, dataBytes) {
    if (address < 0 || address > 65535) {
      throw new Error(`Record (${recordType}) address out of range: ${address}`);
    }
    const byteCount = dataBytes.length;
    if (byteCount > RECORD_DATA_MAX_BYTES) {
      throw new Error(
        `Record (${recordType}) data has too many bytes (${byteCount}).`
      );
    }
    if (!isRecordTypeValid(recordType)) {
      throw new Error(`Record type '${recordType}' is not valid.`);
    }
    const recordContent = concatUint8Arrays([
      new Uint8Array([byteCount, address >> 8, address & 255, recordType]),
      dataBytes
    ]);
    const recordContentStr = byteArrayToHexStr(recordContent);
    const checksumStr = byteToHexStrFast(calcChecksumByte(recordContent));
    return `${START_CODE_STR}${recordContentStr}${checksumStr}`;
  }
  function validateRecord(iHexRecord) {
    if (iHexRecord.length < MIN_RECORD_STR_LEN) {
      throw new Error(`Record length too small: ${iHexRecord}`);
    }
    if (iHexRecord.length > MAX_RECORD_STR_LEN) {
      throw new Error(`Record length is too large: ${iHexRecord}`);
    }
    if (iHexRecord[0] !== ":") {
      throw new Error(`Record does not start with a ":": ${iHexRecord}`);
    }
    return true;
  }
  function getRecordType(iHexRecord) {
    validateRecord(iHexRecord);
    const recordTypeCharStart = START_CODE_STR_LEN + BYTE_COUNT_STR_LEN + ADDRESS_STR_LEN;
    const recordTypeStr = iHexRecord.slice(
      recordTypeCharStart,
      recordTypeCharStart + RECORD_TYPE_STR_LEN
    );
    const recordType = parseInt(recordTypeStr, 16);
    if (!isRecordTypeValid(recordType)) {
      throw new Error(
        `Record type '${recordTypeStr}' from record '${iHexRecord}' is not valid.`
      );
    }
    return recordType;
  }
  function getRecordData(iHexRecord) {
    try {
      return hexStrToBytes(iHexRecord.slice(DATA_STR_INDEX, -2));
    } catch (err) {
      const e = err;
      throw new Error(
        `Could not parse Intel Hex record "${iHexRecord}": ${e.message}`
      );
    }
  }
  function parseRecord(iHexRecord) {
    validateRecord(iHexRecord);
    let recordBytes;
    try {
      recordBytes = hexStrToBytes(iHexRecord.substring(1));
    } catch (err) {
      const e = err;
      throw new Error(
        `Could not parse Intel Hex record "${iHexRecord}": ${e.message}`
      );
    }
    const byteCountIndex = 0;
    const byteCount = recordBytes[0];
    const addressIndex = byteCountIndex + BYTE_COUNT_STR_LEN / 2;
    const address = (recordBytes[addressIndex] << 8) + recordBytes[addressIndex + 1];
    const recordTypeIndex = addressIndex + ADDRESS_STR_LEN / 2;
    const recordType = recordBytes[recordTypeIndex];
    const dataIndex = recordTypeIndex + RECORD_TYPE_STR_LEN / 2;
    const checksumIndex = dataIndex + byteCount;
    const data = recordBytes.slice(dataIndex, checksumIndex);
    const checksum = recordBytes[checksumIndex];
    const totalLength = checksumIndex + CHECKSUM_STR_LEN / 2;
    if (recordBytes.length > totalLength) {
      throw new Error(
        `Parsed record "${iHexRecord}" is larger than indicated by the byte count.
	Expected: ${totalLength}; Length: ${recordBytes.length}.`
      );
    }
    return {
      byteCount,
      address,
      recordType,
      data,
      checksum
    };
  }
  function endOfFileRecord() {
    return ":00000001FF";
  }
  function extLinAddressRecord(address) {
    if (address < 0 || address > 4294967295) {
      throw new Error(
        `Address '${address}' for Extended Linear Address record is out of range.`
      );
    }
    return createRecord(
      0,
      4 /* ExtendedLinearAddress */,
      new Uint8Array([address >> 24 & 255, address >> 16 & 255])
    );
  }
  function blockStartRecord(boardId) {
    if (boardId < 0 || boardId > 65535) {
      throw new Error("Board ID out of range when creating Block Start record.");
    }
    return createRecord(
      0,
      10 /* BlockStart */,
      new Uint8Array([boardId >> 8 & 255, boardId & 255, 192, 222])
    );
  }
  function blockEndRecord(padBytesLen) {
    switch (padBytesLen) {
      case 4:
        return ":0400000BFFFFFFFFF5";
      case 12:
        return ":0C00000BFFFFFFFFFFFFFFFFFFFFFFFFF5";
      default: {
        const recordData = new Uint8Array(padBytesLen).fill(255);
        return createRecord(0, 11 /* BlockEnd */, recordData);
      }
    }
  }
  function paddedDataRecord(padBytesLen) {
    const recordData = new Uint8Array(padBytesLen).fill(255);
    return createRecord(0, 12 /* PaddedData */, recordData);
  }
  function convertRecordTo(iHexRecord, recordType) {
    const oRecord = parseRecord(iHexRecord);
    const recordContent = new Uint8Array(oRecord.data.length + 4);
    recordContent[0] = oRecord.data.length;
    recordContent[1] = oRecord.address >> 8;
    recordContent[2] = oRecord.address & 255;
    recordContent[3] = recordType;
    recordContent.set(oRecord.data, 4);
    const recordContentStr = byteArrayToHexStr(recordContent);
    const checksumStr = byteToHexStrFast(calcChecksumByte(recordContent));
    return `${START_CODE_STR}${recordContentStr}${checksumStr}`;
  }
  function convertExtSegToLinAddressRecord(iHexRecord) {
    const segmentAddress = getRecordData(iHexRecord);
    if (segmentAddress.length !== 2 || segmentAddress[0] & 15 || // Only process multiples of 0x1000
    segmentAddress[1] !== 0) {
      throw new Error(`Invalid Extended Segment Address record ${iHexRecord}`);
    }
    const startAddress = segmentAddress[0] << 12;
    return extLinAddressRecord(startAddress);
  }
  function iHexToRecordStrs(iHexStr) {
    const output = iHexStr.replace(/\r/g, "").split("\n");
    return output.filter(Boolean);
  }
  function findDataFieldLength(iHexRecords) {
    let maxDataBytes = 16;
    let maxDataBytesCount = 0;
    for (const record of iHexRecords) {
      const dataBytesLength = (record.length - MIN_RECORD_STR_LEN) / 2;
      if (dataBytesLength > maxDataBytes) {
        maxDataBytes = dataBytesLength;
        maxDataBytesCount = 0;
      } else if (dataBytesLength === maxDataBytes) {
        maxDataBytesCount++;
      }
      if (maxDataBytesCount > 12) {
        break;
      }
    }
    if (maxDataBytes > RECORD_DATA_MAX_BYTES) {
      throw new Error(`Intel Hex record data size is too large: ${maxDataBytes}`);
    }
    return maxDataBytes;
  }

  // src/universal-hex.ts
  var V1_BOARD_IDS = [39168, 39169];
  var BLOCK_SIZE = 512;
  var microbitBoardId = /* @__PURE__ */ ((microbitBoardId2) => {
    microbitBoardId2[microbitBoardId2["V1"] = 39168] = "V1";
    microbitBoardId2[microbitBoardId2["V2"] = 39171] = "V2";
    return microbitBoardId2;
  })(microbitBoardId || {});
  function iHexToCustomFormatBlocks(iHexStr, boardId) {
    const replaceDataRecord = !V1_BOARD_IDS.includes(boardId);
    const startRecord = blockStartRecord(boardId);
    let currentExtAddr = extLinAddressRecord(0);
    const extAddrRecordLen = currentExtAddr.length;
    const startRecordLen = startRecord.length;
    const endRecordBaseLen = blockEndRecord(0).length;
    const padRecordBaseLen = paddedDataRecord(0).length;
    const hexRecords = iHexToRecordStrs(iHexStr);
    const recordPaddingCapacity = findDataFieldLength(hexRecords);
    if (!hexRecords.length) return "";
    if (isUniversalHexRecords(hexRecords)) {
      throw new Error(`Board ID ${boardId} Hex is already a Universal Hex.`);
    }
    let ih = 0;
    const blockLines = [];
    while (ih < hexRecords.length) {
      let blockLen = 0;
      const firstRecordType = getRecordType(hexRecords[ih]);
      if (firstRecordType === 4 /* ExtendedLinearAddress */) {
        currentExtAddr = hexRecords[ih];
        ih++;
      } else if (firstRecordType === 2 /* ExtendedSegmentAddress */) {
        currentExtAddr = convertExtSegToLinAddressRecord(hexRecords[ih]);
        ih++;
      }
      blockLines.push(currentExtAddr);
      blockLen += extAddrRecordLen + 1;
      blockLines.push(startRecord);
      blockLen += startRecordLen + 1;
      blockLen += endRecordBaseLen + 1;
      let endOfFile = false;
      while (hexRecords[ih] && BLOCK_SIZE >= blockLen + hexRecords[ih].length + 1) {
        let record = hexRecords[ih++];
        const recordType = getRecordType(record);
        if (replaceDataRecord && recordType === 0 /* Data */) {
          record = convertRecordTo(record, 13 /* CustomData */);
        } else if (recordType === 4 /* ExtendedLinearAddress */) {
          currentExtAddr = record;
        } else if (recordType === 2 /* ExtendedSegmentAddress */) {
          record = convertExtSegToLinAddressRecord(record);
          currentExtAddr = record;
        } else if (recordType === 1 /* EndOfFile */) {
          endOfFile = true;
          break;
        }
        blockLines.push(record);
        blockLen += record.length + 1;
      }
      if (endOfFile) {
        if (ih !== hexRecords.length) {
          if (isMakeCodeForV1HexRecords(hexRecords)) {
            throw new Error(
              `Board ID ${boardId} Hex is from MakeCode, import this hex into the MakeCode editor to create a Universal Hex.`
            );
          } else {
            throw new Error(
              `EoF record found at record ${ih} of ${hexRecords.length} in Board ID ${boardId} hex`
            );
          }
        }
        blockLines.push(blockEndRecord(0));
        blockLines.push(endOfFileRecord());
      } else {
        while (BLOCK_SIZE - blockLen > recordPaddingCapacity * 2) {
          const record = paddedDataRecord(
            Math.min(
              (BLOCK_SIZE - blockLen - (padRecordBaseLen + 1)) / 2,
              recordPaddingCapacity
            )
          );
          blockLines.push(record);
          blockLen += record.length + 1;
        }
        blockLines.push(blockEndRecord((BLOCK_SIZE - blockLen) / 2));
      }
    }
    blockLines.push("");
    return blockLines.join("\n");
  }
  function iHexToCustomFormatSection(iHexStr, boardId) {
    const sectionLines = [];
    let sectionLen = 0;
    let ih = 0;
    const addRecordLength = (record) => {
      sectionLen += record.length + 1;
    };
    const addRecord = (record) => {
      sectionLines.push(record);
      addRecordLength(record);
    };
    const hexRecords = iHexToRecordStrs(iHexStr);
    if (!hexRecords.length) return "";
    if (isUniversalHexRecords(hexRecords)) {
      throw new Error(`Board ID ${boardId} Hex is already a Universal Hex.`);
    }
    const iHexFirstRecordType = getRecordType(hexRecords[0]);
    if (iHexFirstRecordType === 4 /* ExtendedLinearAddress */) {
      addRecord(hexRecords[0]);
      ih++;
    } else if (iHexFirstRecordType === 2 /* ExtendedSegmentAddress */) {
      addRecord(convertExtSegToLinAddressRecord(hexRecords[0]));
      ih++;
    } else {
      addRecord(extLinAddressRecord(0));
    }
    addRecord(blockStartRecord(boardId));
    const replaceDataRecord = !V1_BOARD_IDS.includes(boardId);
    let endOfFile = false;
    while (ih < hexRecords.length) {
      const record = hexRecords[ih++];
      const recordType = getRecordType(record);
      if (recordType === 0 /* Data */) {
        addRecord(
          replaceDataRecord ? convertRecordTo(record, 13 /* CustomData */) : record
        );
      } else if (recordType === 2 /* ExtendedSegmentAddress */) {
        addRecord(convertExtSegToLinAddressRecord(record));
      } else if (recordType === 4 /* ExtendedLinearAddress */) {
        addRecord(record);
      } else if (recordType === 1 /* EndOfFile */) {
        endOfFile = true;
        break;
      }
    }
    if (ih !== hexRecords.length) {
      if (isMakeCodeForV1HexRecords(hexRecords)) {
        throw new Error(
          `Board ID ${boardId} Hex is from MakeCode, import this hex into the MakeCode editor to create a Universal Hex.`
        );
      } else {
        throw new Error(
          `EoF record found at record ${ih} of ${hexRecords.length} in Board ID ${boardId} hex `
        );
      }
    }
    addRecordLength(blockEndRecord(0));
    const recordNoDataLenChars = paddedDataRecord(0).length + 1;
    const recordDataMaxBytes = findDataFieldLength(hexRecords);
    const paddingCapacityChars = recordDataMaxBytes * 2;
    let charsNeeded = (BLOCK_SIZE - sectionLen % BLOCK_SIZE) % BLOCK_SIZE;
    while (charsNeeded > paddingCapacityChars) {
      const byteLen = charsNeeded - recordNoDataLenChars >> 1;
      const record = paddedDataRecord(Math.min(byteLen, recordDataMaxBytes));
      addRecord(record);
      charsNeeded = (BLOCK_SIZE - sectionLen % BLOCK_SIZE) % BLOCK_SIZE;
    }
    sectionLines.push(blockEndRecord(charsNeeded >> 1));
    if (endOfFile) sectionLines.push(endOfFileRecord());
    sectionLines.push("");
    return sectionLines.join("\n");
  }
  function createUniversalHex(hexes, blocks = false) {
    if (!hexes.length) return "";
    const iHexToCustomFormat = blocks ? iHexToCustomFormatBlocks : iHexToCustomFormatSection;
    const eofNlRecord = endOfFileRecord() + "\n";
    const customHexes = [];
    for (let i = 0; i < hexes.length - 1; i++) {
      let customHex = iHexToCustomFormat(hexes[i].hex, hexes[i].boardId);
      if (customHex.endsWith(eofNlRecord)) {
        customHex = customHex.slice(0, customHex.length - eofNlRecord.length);
      }
      customHexes.push(customHex);
    }
    const lastCustomHex = iHexToCustomFormat(
      hexes[hexes.length - 1].hex,
      hexes[hexes.length - 1].boardId
    );
    customHexes.push(lastCustomHex);
    if (!lastCustomHex.endsWith(eofNlRecord)) {
      customHexes.push(eofNlRecord);
    }
    return customHexes.join("");
  }
  function isUniversalHex(hexStr) {
    const elaRecordBeginning = ":02000004";
    if (hexStr.slice(0, elaRecordBeginning.length) !== elaRecordBeginning) {
      return false;
    }
    let i = elaRecordBeginning.length;
    while (hexStr[++i] !== ":" && i < MAX_RECORD_STR_LEN + 3) ;
    const blockStartBeginning = ":0400000A";
    if (hexStr.slice(i, i + blockStartBeginning.length) !== blockStartBeginning) {
      return false;
    }
    return true;
  }
  function isUniversalHexRecords(records) {
    return getRecordType(records[0]) === 4 /* ExtendedLinearAddress */ && getRecordType(records[1]) === 10 /* BlockStart */ && getRecordType(records[records.length - 1]) === 1 /* EndOfFile */;
  }
  function isMakeCodeForV1HexRecords(records) {
    let i = records.indexOf(endOfFileRecord());
    if (i === records.length - 1) {
      while (--i > 0) {
        if (records[i] === extLinAddressRecord(536870912)) {
          return true;
        }
      }
    }
    while (++i < records.length) {
      if (getRecordType(records[i]) === 14 /* OtherData */) {
        return true;
      }
      if (records[i] === extLinAddressRecord(536870912)) {
        return true;
      }
    }
    return false;
  }
  function isMakeCodeForV1Hex(hexStr) {
    return isMakeCodeForV1HexRecords(iHexToRecordStrs(hexStr));
  }
  function separateUniversalHex(universalHexStr) {
    const records = iHexToRecordStrs(universalHexStr);
    if (!records.length) throw new Error("Empty Universal Hex.");
    if (!isUniversalHexRecords(records)) {
      throw new Error("Universal Hex format invalid.");
    }
    const passThroughRecords = [
      0 /* Data */,
      1 /* EndOfFile */,
      2 /* ExtendedSegmentAddress */,
      3 /* StartSegmentAddress */
    ];
    const hexes = {};
    let currentBoardId = 0;
    for (let i = 0; i < records.length; i++) {
      const record = records[i];
      const recordType = getRecordType(record);
      if (passThroughRecords.includes(recordType)) {
        hexes[currentBoardId].hex.push(record);
      } else if (recordType === 13 /* CustomData */) {
        hexes[currentBoardId].hex.push(
          convertRecordTo(record, 0 /* Data */)
        );
      } else if (recordType === 4 /* ExtendedLinearAddress */) {
        const nextRecord = records[i + 1];
        if (getRecordType(nextRecord) === 10 /* BlockStart */) {
          const blockStartData = getRecordData(nextRecord);
          if (blockStartData.length !== 4) {
            throw new Error(`Block Start record invalid: ${nextRecord}`);
          }
          currentBoardId = (blockStartData[0] << 8) + blockStartData[1];
          hexes[currentBoardId] = hexes[currentBoardId] || {
            boardId: currentBoardId,
            lastExtAdd: record,
            hex: [record]
          };
          i++;
        }
        if (hexes[currentBoardId].lastExtAdd !== record) {
          hexes[currentBoardId].lastExtAdd = record;
          hexes[currentBoardId].hex.push(record);
        }
      }
    }
    const returnArray = [];
    Object.keys(hexes).forEach((boardId) => {
      const hex = hexes[boardId].hex;
      if (hex[hex.length - 1] !== endOfFileRecord()) {
        hex[hex.length] = endOfFileRecord();
      }
      returnArray.push({
        boardId: hexes[boardId].boardId,
        hex: hex.join("\n") + "\n"
      });
    });
    return returnArray;
  }
  return __toCommonJS(index_exports);
})();
