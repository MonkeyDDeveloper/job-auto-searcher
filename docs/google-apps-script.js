const SPREADSHEET_ID = '1I_QuiLT5TQLBcDA3Cc7Ttw7fia9huQ5AL2XrcFQowI0';
const SHEET_NAME = 'Hoja 1';
const SECRET = 'REPLACE_WITH_GOOGLE_APPS_SCRIPT_TOKEN';
const HEADERS = [
  'id', 'uri', 'candidato', 'cargo', 'empresa', 'ubicacion', 'modalidad',
  'score', 'rango_salarial', 'email_contacto', 'email_recomendado',
  'justificacion', 'postulada', 'fecha_creacion', 'fecha_postulacion'
];

function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents || '{}');
    if (body.token !== SECRET) return jsonResponse({ ok: false, error: 'Unauthorized' });

    if (body.action === 'list') return listRows();
    if (body.action === 'append') return appendRows(body.rows || []);
    if (body.action === 'mark_applied') return markApplied(String(body.id || ''));

    return jsonResponse({ ok: false, error: 'Unknown action' });
  } catch (error) {
    return jsonResponse({ ok: false, error: String(error) });
  }
}

function getSheet() {
  return SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName(SHEET_NAME);
}

function ensureHeaders(sheet) {
  if (sheet.getLastRow() === 0) {
    sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
    return HEADERS;
  }
  const current = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  const headers = current.length ? current : [];
  const missing = HEADERS.filter(header => headers.indexOf(header) < 0);
  if (missing.length) {
    sheet.getRange(1, headers.length + 1, 1, missing.length).setValues([missing]);
    return headers.concat(missing);
  }
  return headers;
}

function listRows() {
  const sheet = getSheet();
  const headers = ensureHeaders(sheet);
  if (sheet.getLastRow() < 2) return jsonResponse({ ok: true, rows: [] });

  const values = sheet.getRange(2, 1, sheet.getLastRow() - 1, headers.length).getValues();
  const rows = values.map(row => {
    const item = {};
    headers.forEach((header, index) => item[header] = row[index] == null ? '' : String(row[index]));
    return item;
  });
  return jsonResponse({ ok: true, rows });
}

function appendRows(rows) {
  const sheet = getSheet();
  const headers = ensureHeaders(sheet);
  const now = new Date();
  const values = rows.map(item => headers.map(header => {
    if (header === 'fecha_creacion') return now;
    if (header === 'postulada') return item[header] || 'no';
    return item[header] == null ? '' : item[header];
  }));
  if (values.length) sheet.getRange(sheet.getLastRow() + 1, 1, values.length, headers.length).setValues(values);
  return jsonResponse({ ok: true, appended: values.length });
}

function markApplied(id) {
  const sheet = getSheet();
  const headers = ensureHeaders(sheet);
  const idColumn = headers.indexOf('id');
  const appliedColumn = headers.indexOf('postulada');
  const dateColumn = headers.indexOf('fecha_postulacion');
  if (idColumn < 0 || appliedColumn < 0) return jsonResponse({ ok: false, error: 'Missing columns' });

  const values = sheet.getDataRange().getValues();
  for (let row = 1; row < values.length; row++) {
    if (String(values[row][idColumn]) !== id) continue;
    const current = String(values[row][appliedColumn]).toLowerCase();
    if (current === 'si' || current === 'sí') {
      return jsonResponse({ ok: true, message: 'La postulación ya estaba marcada como postulada.' });
    }
    sheet.getRange(row + 1, appliedColumn + 1).setValue('si');
    if (dateColumn >= 0) sheet.getRange(row + 1, dateColumn + 1).setValue(new Date());
    return jsonResponse({ ok: true, message: 'La postulación fue marcada como postulada.' });
  }
  return jsonResponse({ ok: false, error: 'Postulación no encontrada' });
}

function jsonResponse(data) {
  return ContentService.createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}
