import { APP_CONFIG } from "./config.js";
import { DEMO_REPORTS } from "./demo-data.js";

const LOCAL_STORAGE_KEY = "school-neighborhood-gis-reports-v1";

function hasSupabaseConfig() {
  const { supabaseUrl, supabaseAnonKey, useSupabaseWhenConfigured } = APP_CONFIG.storage;
  return Boolean(
    useSupabaseWhenConfigured &&
      supabaseUrl &&
      supabaseAnonKey &&
      !supabaseUrl.includes("YOUR_") &&
      !supabaseAnonKey.includes("YOUR_"),
  );
}

function sortByNewest(records) {
  return [...records].sort((left, right) => new Date(right.createdAt) - new Date(left.createdAt));
}

function toClientRecord(record) {
  return {
    id: record.id,
    kind: record.report_kind ?? record.kind,
    categoryId: record.category_id ?? record.categoryId,
    severity: record.severity,
    title: record.title,
    description: record.description,
    actionHint: record.action_hint ?? record.actionHint ?? "",
    placeHint: record.place_hint ?? record.placeHint ?? "",
    reporterName: record.reporter_name ?? record.reporterName ?? "",
    latitude: Number(record.latitude),
    longitude: Number(record.longitude),
    status: record.status,
    reviewNote: record.review_note ?? record.reviewNote ?? "",
    createdAt: record.created_at ?? record.createdAt,
    reviewedAt: record.reviewed_at ?? record.reviewedAt ?? null,
  };
}

function toDbRecord(record) {
  return {
    report_kind: record.kind,
    category_id: record.categoryId,
    severity: record.severity,
    title: record.title,
    description: record.description,
    action_hint: record.actionHint,
    place_hint: record.placeHint,
    reporter_name: record.reporterName,
    latitude: record.latitude,
    longitude: record.longitude,
    status: record.status,
    review_note: record.reviewNote ?? null,
    reviewed_at: record.reviewedAt ?? null,
  };
}

function createRecordId() {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `local-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
}

class LocalReportStore {
  constructor(options = {}) {
    this.mode = "local";
    this.supportsModeratorSignIn = false;
    this.reason = options.reason ?? "demo";
    this.connectionError = options.connectionError ?? null;
    this._ensureSeedData();
  }

  _ensureSeedData() {
    const raw = window.localStorage.getItem(LOCAL_STORAGE_KEY);
    if (!raw) {
      window.localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(DEMO_REPORTS));
    }
  }

  _read() {
    this._ensureSeedData();
    const raw = window.localStorage.getItem(LOCAL_STORAGE_KEY);
    return raw ? JSON.parse(raw).map(toClientRecord) : [];
  }

  _write(records) {
    window.localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(records));
  }

  async getSession() {
    return { user: { email: APP_CONFIG.moderation.localModeratorLabel } };
  }

  onAuthChange() {
    return () => {};
  }

  async requestModeratorAccess() {
    return { ok: true, message: "데모 모드에서는 즉시 검수할 수 있습니다." };
  }

  async signOutModerator() {
    return;
  }

  async loadApprovedReports() {
    return sortByNewest(this._read().filter((record) => record.status === "approved"));
  }

  async loadPendingReports() {
    return sortByNewest(this._read().filter((record) => record.status === "pending"));
  }

  async createReport(input) {
    const records = this._read();
    const record = {
      ...input,
      id: createRecordId(),
      status: "pending",
      createdAt: new Date().toISOString(),
      reviewedAt: null,
      reviewNote: "",
    };
    records.push(record);
    this._write(records);
    return record;
  }

  async updateReportStatus(id, status, reviewNote = "") {
    const records = this._read();
    const nextRecords = records.map((record) => {
      if (record.id !== id) {
        return record;
      }
      return {
        ...record,
        status,
        reviewNote,
        reviewedAt: new Date().toISOString(),
      };
    });
    this._write(nextRecords);
    return nextRecords.find((record) => record.id === id) ?? null;
  }
}

class SupabaseReportStore {
  constructor(client) {
    this.client = client;
    this.mode = "supabase";
    this.supportsModeratorSignIn = true;
    this.tableName = APP_CONFIG.storage.tableName;
    this.reason = "connected";
    this.connectionError = null;
  }

  async getSession() {
    const { data, error } = await this.client.auth.getSession();
    if (error) {
      throw error;
    }
    return data.session;
  }

  onAuthChange(handler) {
    const {
      data: { subscription },
    } = this.client.auth.onAuthStateChange((_event, session) => {
      handler(session);
    });
    return () => subscription.unsubscribe();
  }

  async requestModeratorAccess(email) {
    const { error } = await this.client.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: window.location.href,
      },
    });

    if (error) {
      throw error;
    }

    return {
      ok: true,
      message: "인증 메일을 보냈습니다. 메일의 링크를 눌러 검수 화면으로 돌아오세요.",
    };
  }

  async signOutModerator() {
    const { error } = await this.client.auth.signOut();
    if (error) {
      throw error;
    }
  }

  async loadApprovedReports() {
    const { data, error } = await this.client
      .from(this.tableName)
      .select("*")
      .eq("status", "approved")
      .order("created_at", { ascending: false });

    if (error) {
      throw error;
    }

    return data.map(toClientRecord);
  }

  async loadPendingReports() {
    const { data, error } = await this.client
      .from(this.tableName)
      .select("*")
      .eq("status", "pending")
      .order("created_at", { ascending: false });

    if (error) {
      throw error;
    }

    return data.map(toClientRecord);
  }

  async createReport(input) {
    const payload = toDbRecord({
      ...input,
      status: "pending",
    });

    const { data, error } = await this.client
      .from(this.tableName)
      .insert(payload)
      .select("*")
      .single();

    if (error) {
      throw error;
    }

    return toClientRecord(data);
  }

  async updateReportStatus(id, status, reviewNote = "") {
    const { data, error } = await this.client
      .from(this.tableName)
      .update({
        status,
        review_note: reviewNote || null,
        reviewed_at: new Date().toISOString(),
      })
      .eq("id", id)
      .select("*")
      .single();

    if (error) {
      throw error;
    }

    return toClientRecord(data);
  }
}

async function probeSupabaseConnection(client, tableName) {
  const { error } = await client.from(tableName).select("id", { head: true, count: "exact" }).limit(1);
  if (error) {
    throw error;
  }
}

export async function createReportStore() {
  if (!hasSupabaseConfig()) {
    return new LocalReportStore({ reason: "missing-config" });
  }

  try {
    const { createClient } = await import("https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm");
    const client = createClient(APP_CONFIG.storage.supabaseUrl, APP_CONFIG.storage.supabaseAnonKey, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
      },
    });

    await probeSupabaseConnection(client, APP_CONFIG.storage.tableName);
    return new SupabaseReportStore(client);
  } catch (error) {
    console.error("Supabase bootstrap failed. Falling back to local store.", error);
    return new LocalReportStore({
      reason: "connection-failed",
      connectionError: error,
    });
  }
}
