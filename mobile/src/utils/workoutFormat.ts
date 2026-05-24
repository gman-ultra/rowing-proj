const MM_SS_RE = /^(\d{1,3}):([0-5]\d)$/;
const POSITIVE_NUMBER_RE = /^\d+(?:\.\d+)?$/;
const POSITIVE_INTEGER_RE = /^\d+$/;
const DATE_INPUT_RE = /^(\d{4})-(\d{2})-(\d{2})$/;

export function parseDurationToSeconds(input: string): number | null {
  if (!MM_SS_RE.test(input)) return null;
  const [, mins, secs] = input.match(MM_SS_RE)!;
  const totalSeconds = parseInt(mins, 10) * 60 + parseInt(secs, 10);
  return totalSeconds > 0 ? totalSeconds : null;
}

export function parsePositiveNumber(input: string): number | undefined | null {
  const value = input.trim();
  if (!value) return undefined;
  if (!POSITIVE_NUMBER_RE.test(value)) return null;
  const parsed = Number(value);
  return parsed > 0 ? parsed : null;
}

export function parsePositiveInteger(input: string): number | undefined | null {
  const value = input.trim();
  if (!value) return undefined;
  if (!POSITIVE_INTEGER_RE.test(value)) return null;
  const parsed = Number(value);
  return parsed > 0 ? parsed : null;
}

export function formatDuration(totalSeconds: number | null): string {
  if (totalSeconds == null || totalSeconds < 0) return '--:--';
  const mins = Math.floor(totalSeconds / 60);
  const secs = Math.floor(totalSeconds % 60);
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

export function formatSplit(secondsPer500m: number | null): string {
  if (secondsPer500m == null || secondsPer500m <= 0) return '--:--';
  return formatDuration(secondsPer500m);
}

export function formatDistance(meters: number | null): string {
  if (meters == null) return '0m';
  if (meters >= 1000) {
    const km = meters / 1000;
    return `${km.toFixed(2)}km`;
  }
  return `${Math.round(meters)}m`;
}

function parseDateInputParts(input: string): { year: number; month: number; day: number } | null {
  const value = input.trim();
  const match = value.match(DATE_INPUT_RE);
  if (!match) return null;

  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const parsed = new Date(year, month - 1, day);

  if (
    parsed.getFullYear() !== year ||
    parsed.getMonth() !== month - 1 ||
    parsed.getDate() !== day
  ) {
    return null;
  }

  return { year, month, day };
}

export function isValidDateInput(input: string): boolean {
  return parseDateInputParts(input) !== null;
}

export function formatDateForInput(date: Date): string {
  return [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, '0'),
    String(date.getDate()).padStart(2, '0'),
  ].join('-');
}

export function getTodayLocalDateInput(): string {
  return formatDateForInput(new Date());
}

function parseApiWorkoutDate(dateString: string): Date | null {
  if (!dateString) return null;

  // Keep date-only values as local calendar dates. JS treats
  // new Date('YYYY-MM-DD') as UTC, which can display as the previous day in
  // negative-offset time zones.
  const dateOnlyParts = parseDateInputParts(dateString);
  if (dateOnlyParts && /^\d{4}-\d{2}-\d{2}$/.test(dateString.trim())) {
    return new Date(dateOnlyParts.year, dateOnlyParts.month - 1, dateOnlyParts.day);
  }

  // FastAPI serializes naive datetimes without an offset. Server-generated
  // fallback dates were UTC, so treating timezone-less datetime strings as
  // local time can shift "today" into tomorrow on phones in US time zones.
  // Append Z for datetime strings without an explicit zone.
  const hasTimezone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(dateString);
  const normalized = !hasTimezone ? `${dateString}Z` : dateString;
  const parsed = new Date(normalized);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

export function formatWorkoutDate(dateString: string): string {
  const parsed = parseApiWorkoutDate(dateString);
  if (!parsed) return dateString;
  return parsed.toLocaleDateString();
}

export function formatWorkoutDateTime(dateString: string): string {
  const parsed = parseApiWorkoutDate(dateString);
  if (!parsed) return dateString;
  return parsed.toLocaleString();
}

export function getWorkoutDateInputValue(dateString: string): string {
  const parsed = parseApiWorkoutDate(dateString);
  if (!parsed) {
    return dateString.slice(0, 10);
  }
  return formatDateForInput(parsed);
}

export function buildLocalNoonWorkoutDate(dateInput: string): string | null {
  const parts = parseDateInputParts(dateInput);
  if (!parts) return null;
  return `${dateInput.trim()}T12:00:00`;
}

export function getWorkoutTimeValue(dateString: string): number {
  const parsed = parseApiWorkoutDate(dateString);
  return parsed?.getTime() ?? 0;
}

export function getWorkoutDisplayName(workoutName: string | null | undefined): string {
  const value = workoutName?.trim();
  return value ? value : 'Erg Workout';
}

function getStartOfLocalDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate());
}

export function getWorkoutLocalDay(dateString: string): Date | null {
  const parsed = parseApiWorkoutDate(dateString);
  if (!parsed) return null;
  return getStartOfLocalDay(parsed);
}

export function isWorkoutInLastLocalDays(dateString: string, days: number): boolean {
  const workoutDay = getWorkoutLocalDay(dateString);
  if (!workoutDay) return false;

  const today = getStartOfLocalDay(new Date());
  const diffMs = today.getTime() - workoutDay.getTime();
  const diffDays = Math.round(diffMs / (24 * 60 * 60 * 1000));

  return diffDays >= 0 && diffDays < days;
}
