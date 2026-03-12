//Code for the App Script
/**
 * BME280 Data Logger - Apps Script
 * Student: Piyumi Tihara Egodage
 * ID: 20220318 w1953194
 * Purpose: Receive and log IoT BME280 sensor data
 */

// Configuration
const SHEET_NAME = "w1953194_6NTCM009W_CW";
const MAX_ROWS = 500; // Prevent unlimited growth

/**
 * Handle POST requests from Pico W
 * Expects JSON: {temperature, pressure, humidity}
 */
function doPost(e) {
  try {
    // Log incoming request for debugging
    Logger.log("Received POST request");

    // Parse JSON data
    const data = JSON.parse(e.postData.contents);
    Logger.log("Parsed data: " + JSON.stringify(data));

    // Get active spreadsheet and target sheet
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);

    if (!sheet) {
      throw new Error(`Sheet "${SHEET_NAME}" not found`);
    }

    // Get current entry count
    const lastRow = sheet.getLastRow();
    const entryNumber = lastRow + 1;

    // Create timestamp
    const timestamp = new Date();

    // Prepare row data
    const rowData = [
      timestamp,
      parseFloat(data.temperature) || 0,
      parseFloat(data.pressure) || 0,
      parseFloat(data.humidity) || 0,
      entryNumber
    ];

    // Append data to sheet
    sheet.appendRow(rowData);

    // To format the new row
    const newRow = sheet.getLastRow();

    sheet.getRange(newRow, 1).setNumberFormat("yyyy-mm-dd hh:mm:ss");

    // Format number columns (2 decimal places)
    for (let col = 2; col <= 6; col++) {
      sheet.getRange(newRow, col).setNumberFormat("0.00");
    }

    // Auto-resize columns if first data entry
    if (newRow === 2) {
      sheet.autoResizeColumns(1, 5);
    }

    // Prevent sheet from growing too large
    if (lastRow > MAX_ROWS) {
      sheet.deleteRow(2); // Delete oldest data (row 2, keeping headers)
    }

    // Return success response
    const response = {
      status: "success",
      entry: entryNumber,
      timestamp: timestamp.toISOString(),
      message: `Data logged successfully (Entry #${entryNumber})`
    };

    Logger.log("Response: " + JSON.stringify(response));

    return ContentService
      .createTextOutput(JSON.stringify(response))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    // Log error
    Logger.log("Error: " + error.toString());

    // Return error response
    const errorResponse = {
      status: "error",
      message: error.toString()
    };

    return ContentService
      .createTextOutput(JSON.stringify(errorResponse))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Calculate statistics - not in use as of now
 */
function calculateStatistics() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  const lastRow = sheet.getLastRow();

  if (lastRow < 2) return null;

  // Get temperature column (B)
  const tempRange = sheet.getRange(2, 2, lastRow - 1, 1);
  const temps = tempRange.getValues().flat();

  return {
    count: temps.length,
    min: Math.min(...temps),
    max: Math.max(...temps),
    average: temps.reduce((a, b) => a + b, 0) / temps.length
  };
}
