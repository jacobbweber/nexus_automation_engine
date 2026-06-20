import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "@/app/AppShell";
import { AuthProvider, useAuth } from "@/app/auth";
import { ModeProvider } from "@/shared/theme/mode";
import { PrefsProvider } from "@/shared/theme/prefs";
import { ThemesProvider } from "@/shared/theme/theme-provider";
import { LoginPage } from "@/features/auth/LoginPage";
import { CanvasPage } from "@/features/canvas/CanvasPage";
import { CatalogPage } from "@/features/catalog/CatalogPage";
import { WorkflowLibraryPage } from "@/features/library/WorkflowLibraryPage";
import { ThemeStudioPage } from "@/features/theme-studio/ThemeStudioPage";
import { AccessibilityPage } from "@/features/accessibility/AccessibilityPage";
import { CmdbSchemaPage } from "@/features/cmdb-schema/CmdbSchemaPage";
import { ConsolePage } from "@/features/console/ConsolePage";
import { AdminPage } from "@/features/admin/AdminPage";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { GovernancePage } from "@/features/governance/GovernancePage";
import { IncidentsPage } from "@/features/incidents/IncidentsPage";

function Protected() {
  const { user, loading } = useAuth();
  if (loading) {
    return <div style={{ padding: 40, color: "var(--text-muted)" }}>Loading…</div>;
  }
  if (!user) return <Navigate to="/login" replace />;
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/catalog" element={<CatalogPage />} />
        <Route path="/canvas" element={<CanvasPage />} />
        <Route path="/library" element={<WorkflowLibraryPage />} />
        <Route path="/theme-studio" element={<ThemeStudioPage />} />
        <Route path="/accessibility" element={<AccessibilityPage />} />
        <Route path="/console" element={<ConsolePage />} />
        <Route path="/governance" element={<GovernancePage />} />
        <Route path="/incidents" element={<IncidentsPage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/cmdb-schema" element={<CmdbSchemaPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppShell>
  );
}

export default function App() {
  return (
    <ModeProvider>
      <ThemesProvider>
        <PrefsProvider>
          <AuthProvider>
            <BrowserRouter>
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/*" element={<Protected />} />
              </Routes>
            </BrowserRouter>
          </AuthProvider>
        </PrefsProvider>
      </ThemesProvider>
    </ModeProvider>
  );
}
