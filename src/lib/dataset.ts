import Papa from 'papaparse';
import * as XLSX from 'xlsx';

export type ColType = 'number' | 'date' | 'category' | 'text' | 'boolean';

export interface ColumnProfile {
  name: string;
  type: ColType;
  missing: number;
  missingPct: number;
  unique: number;
  uniquePct: number;
  // numeric
  min?: number;
  max?: number;
  mean?: number;
  median?: number;
  std?: number;
  q1?: number;
  q3?: number;
  outliers?: number;
  // categorical
  topValues?: { value: string; count: number }[];
  // date
  minDate?: string;
  maxDate?: string;
}

export interface DatasetProfile {
  rowCount: number;
  colCount: number;
  columns: ColumnProfile[];
  duplicates: number;
  duplicatePct: number;
  totalMissing: number;
  totalMissingPct: number;
  numericCols: string[];
  categoricalCols: string[];
  dateCols: string[];
  targetCandidates: string[];
  dateCol: string | null;
  summary: string;
  preview: Record<string, unknown>[];
  raw: Record<string, unknown>[];
}

const DATE_REGEX = /^\d{4}-\d{1,2}-\d{1,2}(?:[ T]\d{2}:\d{2}.*)?$/;
const SLASH_DATE = /^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$/;

function isDateLike(v: unknown): boolean {
  if (v == null) return false;
  if (v instanceof Date) return true;
  const s = String(v);
  return DATE_REGEX.test(s) || SLASH_DATE.test(s);
}

function toDate(v: unknown): number | null {
  if (v == null) return null;
  if (v instanceof Date) return v.getTime();
  const s = String(v).trim();
  let t: number;
  if (DATE_REGEX.test(s) || SLASH_DATE.test(s)) {
    t = new Date(s).getTime();
  } else {
    // try Excel serial-ish numeric date
    const n = Number(s);
    if (!Number.isNaN(n) && n > 20000 && n < 60000) {
      t = new Date((n - 25569) * 86400 * 1000).getTime();
    } else return null;
  }
  return Number.isNaN(t) ? null : t;
}

function isNumber(v: unknown): boolean {
  if (v == null || v === '') return false;
  const n = Number(String(v).replace(/[$,€£%]/g, '').replace(/[()]/g, ''));
  return !Number.isNaN(n) && isFinite(n);
}

function toNumber(v: unknown): number | null {
  if (v == null || v === '') return null;
  const n = Number(String(v).replace(/[$,€£%]/g, '').replace(/[()]/g, ''));
  return Number.isNaN(n) || !isFinite(n) ? null : n;
}

function quantile(sorted: number[], q: number): number {
  if (sorted.length === 0) return NaN;
  const pos = (sorted.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  return sorted[base + 1] !== undefined
    ? sorted[base] + rest * (sorted[base + 1] - sorted[base])
    : sorted[base];
}

function inferType(values: unknown[]): ColType {
  const nonNull = values.filter((v) => v != null && v !== '');
  if (nonNull.length === 0) return 'text';
  let numCount = 0;
  let dateCount = 0;
  let boolCount = 0;
  for (const v of nonNull) {
    if (typeof v === 'boolean' || v === 'true' || v === 'false' || v === 'TRUE' || v === 'FALSE') {
      boolCount++;
      continue;
    }
    if (isNumber(v)) {
      numCount++;
      continue;
    }
    if (isDateLike(v)) dateCount++;
  }
  const n = nonNull.length;
  if (boolCount / n > 0.8) return 'boolean';
  if (numCount / n > 0.8) return 'number';
  if (dateCount / n > 0.7) return 'date';
  return nonNull.length < Math.max(20, n * 0.05) || new Set(nonNull.map(String)).size < n * 0.5
    ? 'category'
    : 'text';
}

function profileColumn(name: string, values: unknown[]): ColumnProfile {
  const total = values.length;
  const missing = values.filter((v) => v == null || v === '').length;
  const nonNull = values.filter((v) => v != null && v !== '');
  const type = inferType(values);
  const uniqueSet = new Set(nonNull.map((v) => String(v)));
  const unique = uniqueSet.size;
  const base: ColumnProfile = {
    name,
    type,
    missing,
    missingPct: total ? (missing / total) * 100 : 0,
    unique,
    uniquePct: nonNull.length ? (unique / nonNull.length) * 100 : 0,
  };

  if (type === 'number') {
    const nums = nonNull.map(toNumber).filter((n): n is number => n != null).sort((a, b) => a - b);
    if (nums.length) {
      const q1 = quantile(nums, 0.25);
      const q3 = quantile(nums, 0.75);
      const iqr = q3 - q1;
      const lo = q1 - 1.5 * iqr;
      const hi = q3 + 1.5 * iqr;
      const outliers = nums.filter((n) => n < lo || n > hi).length;
      const mean = nums.reduce((a, b) => a + b, 0) / nums.length;
      const std = Math.sqrt(nums.reduce((a, b) => a + (b - mean) ** 2, 0) / nums.length);
      Object.assign(base, {
        min: nums[0],
        max: nums[nums.length - 1],
        mean,
        median: quantile(nums, 0.5),
        std,
        q1,
        q3,
        outliers,
      });
    }
  } else if (type === 'date') {
    const ts = nonNull.map(toDate).filter((t): t is number => t != null).sort((a, b) => a - b);
    if (ts.length) {
      base.minDate = new Date(ts[0]).toISOString().slice(0, 10);
      base.maxDate = new Date(ts[ts.length - 1]).toISOString().slice(0, 10);
    }
  } else if (type === 'category' || type === 'boolean') {
    const counts = new Map<string, number>();
    for (const v of nonNull) {
      const k = String(v);
      counts.set(k, (counts.get(k) ?? 0) + 1);
    }
    base.topValues = [...counts.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8)
      .map(([value, count]) => ({ value, count }));
  }
  return base;
}

function buildSummary(
  profile: Omit<DatasetProfile, 'summary' | 'preview' | 'raw'>,
  fileName: string,
): string {
  const { rowCount, colCount, numericCols, categoricalCols, dateCols, duplicates, totalMissingPct } =
    profile;
  const parts: string[] = [];
  parts.push(
    `This dataset contains ${rowCount.toLocaleString()} rows and ${colCount} columns`,
  );
  if (dateCols.length) {
    parts.push(`spanning a time dimension (${dateCols.join(', ')})`);
  }
  if (numericCols.length) {
    parts.push(`with ${numericCols.length} numeric measures`);
  }
  if (categoricalCols.length) {
    parts.push(`and ${categoricalCols.length} categorical dimensions`);
  }
  let s = parts.join(', ') + '.';
  if (duplicates > 0) s += ` ${duplicates} duplicate rows were detected.`;
  if (totalMissingPct > 0.5) {
    s += ` Approximately ${totalMissingPct.toFixed(1)}% of cells are missing.`;
  }
  s += ` File analyzed: ${fileName}.`;
  return s;
}

export async function parseFile(file: File): Promise<DatasetProfile> {
  const rows: Record<string, unknown>[] = [];
  if (file.name.toLowerCase().endsWith('.csv') || file.type === 'text/csv') {
    const text = await file.text();
    const parsed = Papa.parse<Record<string, unknown>>(text, {
      header: true,
      dynamicTyping: false,
      skipEmptyLines: true,
    });
    rows.push(...(parsed.data as Record<string, unknown>[]));
  } else {
    const buf = await file.arrayBuffer();
    const wb = XLSX.read(buf, { type: 'array', cellDates: true });
    const ws = wb.Sheets[wb.SheetNames[0]];
    const json = XLSX.utils.sheet_to_json<Record<string, unknown>>(ws, {
      defval: null,
      raw: true,
    });
    rows.push(...json);
  }

  if (rows.length === 0) throw new Error('No rows found in file.');
  const headers = Object.keys(rows[0]);
  const columns: ColumnProfile[] = headers.map((h) =>
    profileColumn(h, rows.map((r) => r[h])),
  );

  const numericCols = columns.filter((c) => c.type === 'number').map((c) => c.name);
  const categoricalCols = columns
    .filter((c) => c.type === 'category' || c.type === 'boolean')
    .map((c) => c.name);
  const dateCols = columns.filter((c) => c.type === 'date').map((c) => c.name);

  // duplicates
  const seen = new Set<string>();
  let duplicates = 0;
  for (const r of rows) {
    const key = JSON.stringify(r);
    if (seen.has(key)) duplicates++;
    else seen.add(key);
  }

  const totalMissing = columns.reduce((a, c) => a + c.missing, 0);
  const totalCells = rows.length * columns.length;

  // target candidates: numeric columns with reasonable variance, prefer names like sales/profit/revenue
  const targetCandidates = numericCols
    .filter((c) => {
      const col = columns.find((x) => x.name === c)!;
      return col.std != null && col.std > 0 && col.unique > 2;
    })
    .sort((a, b) => {
      const score = (n: string) =>
        /sales|profit|revenue|cost|price|amount|total|churn|demand|quantity/i.test(n) ? 0 : 1;
      return score(a) - score(b);
    })
    .slice(0, 5);

  const dateCol = dateCols[0] ?? null;

  const partial = {
    rowCount: rows.length,
    colCount: columns.length,
    columns,
    duplicates,
    duplicatePct: rows.length ? (duplicates / rows.length) * 100 : 0,
    totalMissing,
    totalMissingPct: totalCells ? (totalMissing / totalCells) * 100 : 0,
    numericCols,
    categoricalCols,
    dateCols,
    targetCandidates,
    dateCol,
  };

  return {
    ...partial,
    summary: buildSummary(partial, file.name),
    preview: rows.slice(0, 8),
    raw: rows,
  };
}
