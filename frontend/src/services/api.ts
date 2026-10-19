import {
  UserRole,
  ExecutiveDashboardResponse,
  OperationsDashboardResponse,
  TechnicianDashboardResponse,
  KPISummary,
  TimeSeriesPoint,
  DailyPerformanceItem,
  VarianceAttributionReport,
  AIExplanationResponse,
  IngestionBatch,
  QuarantineItem
} from '../types';

let currentRole: UserRole = 'OPERATIONS';

export const setGlobalRole = (role: UserRole) => {
  currentRole = role;
};

export const getGlobalRole = (): UserRole => {
  return currentRole;
};

const getHeaders = (): HeadersInit => {
  return {
    'Content-Type': 'application/json',
    'X-User-Role': currentRole,
  };
};

export const api = {
  // Dashboards
  async getExecutiveDashboard(plantId: string = 'helios-50'): Promise<ExecutiveDashboardResponse> {
    const res = await fetch(`/api/v1/dashboards/executive?plant_id=${plantId}`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error(`Executive dashboard error: ${res.statusText}`);
    return res.json();
  },

  async getOperationsDashboard(plantId: string = 'helios-50'): Promise<OperationsDashboardResponse> {
    const res = await fetch(`/api/v1/dashboards/operations?plant_id=${plantId}`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error(`Operations dashboard error: ${res.statusText}`);
    return res.json();
  },

  async getTechnicianDashboard(plantId: string = 'helios-50'): Promise<TechnicianDashboardResponse> {
    const res = await fetch(`/api/v1/dashboards/technician?plant_id=${plantId}`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error(`Technician dashboard error: ${res.statusText}`);
    return res.json();
  },

  // Analytics & Attribution
  async getKPIs(plantId: string = 'helios-50'): Promise<KPISummary> {
    const res = await fetch(`/api/v1/analytics/kpi?plant_id=${plantId}`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error(`KPI fetch error: ${res.statusText}`);
    return res.json();
  },

  async getTimeSeries(plantId: string = 'helios-50'): Promise<TimeSeriesPoint[]> {
    const res = await fetch(`/api/v1/analytics/timeseries?plant_id=${plantId}`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error(`Timeseries fetch error: ${res.statusText}`);
    return res.json();
  },

  async getAttributionReport(plantId: string = 'helios-50'): Promise<VarianceAttributionReport> {
    const res = await fetch(`/api/v1/attribution/report?plant_id=${plantId}`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error(`Attribution report error: ${res.statusText}`);
    return res.json();
  },

  // AI Intelligence
  async queryAI(question: string, role?: string): Promise<AIExplanationResponse> {
    const res = await fetch(`/api/v1/ai/query`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        question,
        role: role || currentRole,
      }),
    });
    if (!res.ok) throw new Error(`AI query error: ${res.statusText}`);
    return res.json();
  },

  // Ingestion & Quarantine
  async uploadCsv(file: File, fileType: string, plantId: string = 'helios-50'): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_type', fileType);
    formData.append('plant_id', plantId);

    const res = await fetch(`/api/v1/ingestion/upload`, {
      method: 'POST',
      headers: {
        'X-User-Role': currentRole,
      },
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to upload CSV');
    }
    return res.json();
  },

  async getBatches(): Promise<IngestionBatch[]> {
    const res = await fetch(`/api/v1/ingestion/batches`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error(`Batches fetch error: ${res.statusText}`);
    return res.json();
  },

  async getQuarantinedRecords(batchId?: string): Promise<QuarantineItem[]> {
    const url = batchId ? `/api/v1/ingestion/quarantine?batch_id=${batchId}` : `/api/v1/ingestion/quarantine`;
    const res = await fetch(url, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error(`Quarantine fetch error: ${res.statusText}`);
    return res.json();
  },

  // Investigations
  async getInvestigations(plantId: string = 'helios-50'): Promise<any[]> {
    const res = await fetch(`/api/v1/investigations/list?plant_id=${plantId}`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error(`Investigations fetch error: ${res.statusText}`);
    return res.json();
  },

  async createInvestigation(data: any): Promise<any> {
    const res = await fetch(`/api/v1/investigations/create`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(`Create investigation error: ${res.statusText}`);
    return res.json();
  },

  async updateInvestigation(id: number, data: any): Promise<any> {
    const res = await fetch(`/api/v1/investigations/${id}/update`, {
      method: 'PATCH',
      headers: getHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(`Update investigation error: ${res.statusText}`);
    return res.json();
  },

  // Work Orders
  async getWorkOrders(plantId: string = 'helios-50'): Promise<any[]> {
    const res = await fetch(`/api/v1/work-orders/list?plant_id=${plantId}`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error(`Work orders fetch error: ${res.statusText}`);
    return res.json();
  },

  async createWorkOrder(data: any): Promise<any> {
    const res = await fetch(`/api/v1/work-orders/create`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(`Create work order error: ${res.statusText}`);
    return res.json();
  },

  async verifySafetyAndLOTO(id: number): Promise<any> {
    const res = await fetch(`/api/v1/work-orders/${id}/verify-safety`, {
      method: 'POST',
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error(`Safety verify error: ${res.statusText}`);
    return res.json();
  },

  // Weather
  async getWeatherHistory(plantId: string = 'helios-50'): Promise<any[]> {
    const res = await fetch(`/api/v1/weather/history?plant_id=${plantId}`, {
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error(`Weather history fetch error: ${res.statusText}`);
    return res.json();
  },

  async syncWeather(plantId: string = 'helios-50'): Promise<any> {
    const res = await fetch(`/api/v1/weather/sync?plant_id=${plantId}`, {
      method: 'POST',
      headers: getHeaders(),
    });
    if (!res.ok) throw new Error(`Sync weather error: ${res.statusText}`);
    return res.json();
  },
};
