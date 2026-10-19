import React, { useState, useEffect } from 'react';
import { UserRole } from './types';
import { api, setGlobalRole } from './services/api';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { ExecutiveView } from './views/ExecutiveView';
import { OperationsView } from './views/OperationsView';
import { TechnicianView } from './views/TechnicianView';
import { IngestionView } from './views/IngestionView';
import { InvestigationsView } from './views/InvestigationsView';
import { WorkOrdersView } from './views/WorkOrdersView';
import { WeatherView } from './views/WeatherView';
import { Loader2, AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [currentRole, setCurrentRole] = useState<UserRole>('OPERATIONS');
  const [activeTab, setActiveTab] = useState<string>('operations');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Dashboard data states
  const [execData, setExecData] = useState<any>(null);
  const [opsData, setOpsData] = useState<any>(null);
  const [techData, setTechData] = useState<any>(null);

  const fetchDashboardData = async (role: UserRole) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      if (role === 'CEO') {
        const data = await api.getExecutiveDashboard();
        setExecData(data);
      } else if (role === 'TECHNICIAN') {
        const data = await api.getTechnicianDashboard();
        setTechData(data);
      } else {
        const data = await api.getOperationsDashboard();
        setOpsData(data);
      }
    } catch (err: any) {
      console.error('Dashboard load failed:', err);
      setErrorMessage(err.message || 'Failed to connect to backend service.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    setGlobalRole(currentRole);
    fetchDashboardData(currentRole);
  }, [currentRole]);

  const handleRoleChange = (newRole: UserRole) => {
    setCurrentRole(newRole);
    setGlobalRole(newRole);

    // Contextually switch the tab to match role
    if (newRole === 'CEO') setActiveTab('executive');
    else if (newRole === 'OPERATIONS') setActiveTab('operations');
    else if (newRole === 'TECHNICIAN') setActiveTab('technician');
  };

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    // Align role with chosen tab if appropriate
    if (tab === 'executive' && currentRole !== 'CEO') {
      setCurrentRole('CEO');
      setGlobalRole('CEO');
    } else if (tab === 'operations' && currentRole !== 'OPERATIONS') {
      setCurrentRole('OPERATIONS');
      setGlobalRole('OPERATIONS');
    } else if (tab === 'technician' && currentRole !== 'TECHNICIAN') {
      setCurrentRole('TECHNICIAN');
      setGlobalRole('TECHNICIAN');
    }
  };

  return (
    <div className="min-h-screen bg-[#090D16] text-[#E2E8F0] flex flex-col font-sans selection:bg-blue-600 selection:text-white">
      {/* Top Industrial Navbar */}
      <Navbar
        currentRole={currentRole}
        onRoleChange={handleRoleChange}
        onRefresh={() => fetchDashboardData(currentRole)}
        isLoading={isLoading}
      />

      {/* Main App Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar */}
        <Sidebar
          activeTab={activeTab}
          onTabChange={handleTabChange}
          currentRole={currentRole}
        />

        {/* Dynamic Content View Area */}
        <main className="flex-1 overflow-y-auto p-6 max-w-7xl mx-auto w-full">
          {errorMessage && (
            <div className="mb-6 p-4 rounded-xl bg-rose-950/40 border border-rose-500/40 flex items-center justify-between text-rose-200 text-xs shadow-lg">
              <div className="flex items-center space-x-2">
                <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
                <span>Backend Connection Error: {errorMessage}</span>
              </div>
              <button
                onClick={() => fetchDashboardData(currentRole)}
                className="px-3 py-1 bg-rose-600 hover:bg-rose-500 text-white rounded text-[11px] font-semibold transition-colors"
              >
                Retry
              </button>
            </div>
          )}

          {isLoading && !execData && !opsData && !techData ? (
            <div className="h-[60vh] flex flex-col items-center justify-center space-y-3 text-gray-500">
              <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
              <p className="text-xs font-mono">Synthesizing plant performance intelligence...</p>
            </div>
          ) : (
            <>
              {activeTab === 'executive' && (
                <ExecutiveView
                  data={execData}
                  onRefresh={() => fetchDashboardData('CEO')}
                />
              )}

              {activeTab === 'operations' && (
                <OperationsView
                  data={opsData}
                  onRefresh={() => fetchDashboardData('OPERATIONS')}
                  onNavigateToInvestigations={() => setActiveTab('investigations')}
                />
              )}

              {activeTab === 'technician' && (
                <TechnicianView
                  data={techData}
                  onRefresh={() => fetchDashboardData('TECHNICIAN')}
                />
              )}

              {activeTab === 'ingestion' && <IngestionView />}

              {activeTab === 'investigations' && <InvestigationsView />}

              {activeTab === 'workorders' && <WorkOrdersView />}

              {activeTab === 'weather' && <WeatherView />}
            </>
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
